from fastapi import APIRouter, HTTPException, Request, Response, status

from app.api.deps import CurrentUser, SessionDep
from app.core.config import get_settings
from app.core.rate_limit import enforce_rate_limit
from app.core.request import client_ip
from app.models.audit import AuditAction
from app.schemas.auth import TokenResponse
from app.schemas.user import LoginRequest, UserPublic
from app.services import audit as audit_service
from app.models.user import User
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=token,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path=settings.refresh_cookie_path,
        max_age=settings.refresh_cookie_max_age,
    )


def _clear_refresh_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path=settings.refresh_cookie_path,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
    )


def _token_response(access_token: str, expires_in: int) -> TokenResponse:
    return TokenResponse(access_token=access_token, expires_in=expires_in)


def _read_refresh_cookie(request: Request) -> str | None:
    return request.cookies.get(get_settings().refresh_cookie_name)


def _enforce_auth_rate_limit(request: Request) -> None:
    settings = get_settings()
    ip = client_ip(request) or "unknown"
    enforce_rate_limit(f"auth:{ip}", settings.auth_rate_limit_per_minute)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    session: SessionDep,
) -> TokenResponse:
    _enforce_auth_rate_limit(request)
    ip = client_ip(request)
    try:
        issued = await auth_service.login(session, str(body.email), body.password)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            await audit_service.record(
                session,
                action=AuditAction.auth_login_failed,
                summary=f"Failed login for {body.email}",
                ip_address=ip,
                metadata={"email": str(body.email).lower()},
            )
        raise
    user = await auth_service.get_user_by_email(session, str(body.email))
    if user is not None:
        await audit_service.record(
            session,
            action=AuditAction.auth_login_success,
            summary=f"User {user.email} signed in",
            actor_user_id=user.id,
            ip_address=ip,
        )
    _set_refresh_cookie(response, issued.refresh_token)
    return _token_response(issued.access_token, issued.expires_in)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response, session: SessionDep) -> TokenResponse:
    _enforce_auth_rate_limit(request)
    issued = await auth_service.refresh(session, _read_refresh_cookie(request))
    _set_refresh_cookie(response, issued.refresh_token)
    return _token_response(issued.access_token, issued.expires_in)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, session: SessionDep) -> None:
    user_id = await auth_service.logout(session, _read_refresh_cookie(request))
    if user_id is not None:
        user = await session.get(User, user_id)
        email = user.email if user is not None else str(user_id)
        await audit_service.record(
            session,
            action=AuditAction.auth_logout,
            summary=f"User {email} signed out",
            actor_user_id=user_id,
            ip_address=client_ip(request),
        )
    _clear_refresh_cookie(response)


@router.get("/me", response_model=UserPublic)
async def me(current_user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(current_user)
