import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import TokenError, create_access_token, create_refresh_token, decode_token, hash_token, verify_password
from app.models.user import RefreshToken, User


class IssuedTokens:
    def __init__(self, access_token: str, refresh_token: str, expires_in: int) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_in = expires_in


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


async def _issue(session: AsyncSession, user: User) -> IssuedTokens:
    settings = get_settings()
    access_token = create_access_token(user.id, user.role)
    refresh_token, expires_at = create_refresh_token(user.id)
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=expires_at,
        )
    )
    await session.flush()
    return IssuedTokens(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_seconds,
    )


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    return await session.scalar(select(User).where(User.email == email.lower()))


async def login(session: AsyncSession, email: str, password: str) -> IssuedTokens:
    result = await session.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active or not verify_password(password, user.hashed_password):
        raise _unauthorized("Invalid email or password")
    return await _issue(session, user)


async def refresh(session: AsyncSession, raw_token: str | None) -> IssuedTokens:
    if not raw_token:
        raise _unauthorized("Refresh token missing")
    try:
        payload = decode_token(raw_token)
    except TokenError:
        raise _unauthorized("Refresh token invalid") from None
    if payload.get("type") != "refresh":
        raise _unauthorized("Refresh token invalid")

    stored = await session.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token)))
    now = datetime.now(UTC)
    if stored is None or stored.revoked_at is not None or stored.expires_at <= now:
        raise _unauthorized("Refresh token invalid")

    user = await session.get(User, stored.user_id)
    if user is None or not user.is_active:
        raise _unauthorized("Refresh token invalid")

    stored.revoked_at = now
    return await _issue(session, user)


async def logout(session: AsyncSession, raw_token: str | None) -> uuid.UUID | None:
    if not raw_token:
        return None
    stored = await session.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token)))
    if stored is None or stored.revoked_at is not None:
        return None
    stored.revoked_at = datetime.now(UTC)
    await session.flush()
    return stored.user_id


def parse_user_id(subject: object) -> uuid.UUID:
    try:
        return uuid.UUID(str(subject))
    except (TypeError, ValueError):
        raise _unauthorized("Not authenticated") from None
