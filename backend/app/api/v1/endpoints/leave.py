import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, SessionDep, require_roles
from app.models.user import Role, User
from app.schemas.leave import LeaveBalancePublic, LeaveRequestCreate, LeaveRequestPublic, LeaveReviewBody, LeaveTypePublic
from app.services import leave as leave_service

router = APIRouter(prefix="/leave", tags=["leave"])


@router.get("/types", response_model=list[LeaveTypePublic])
async def list_types(session: SessionDep, _: CurrentUser) -> list[LeaveTypePublic]:
    return await leave_service.list_leave_types(session)


@router.get("/balances/me", response_model=list[LeaveBalancePublic])
async def my_balances(
    session: SessionDep,
    current_user: CurrentUser,
    year: Annotated[int | None, Query()] = None,
) -> list[LeaveBalancePublic]:
    return await leave_service.list_my_balances(session, current_user, year)


@router.get("/requests/me", response_model=list[LeaveRequestPublic])
async def my_requests(session: SessionDep, current_user: CurrentUser) -> list[LeaveRequestPublic]:
    return await leave_service.list_my_requests(session, current_user)


@router.post("/requests", response_model=LeaveRequestPublic, status_code=201)
async def apply_leave(body: LeaveRequestCreate, session: SessionDep, current_user: CurrentUser) -> LeaveRequestPublic:
    return await leave_service.apply_leave(session, current_user, body)


@router.post("/requests/{request_id}/cancel", response_model=LeaveRequestPublic)
async def cancel_leave(request_id: uuid.UUID, session: SessionDep, current_user: CurrentUser) -> LeaveRequestPublic:
    return await leave_service.cancel_leave(session, current_user, request_id)


@router.get("/requests/inbox", response_model=list[LeaveRequestPublic])
async def leave_inbox(
    session: SessionDep,
    current_user: Annotated[User, Depends(require_roles(Role.admin, Role.manager))],
) -> list[LeaveRequestPublic]:
    return await leave_service.list_inbox(session, current_user)


@router.post("/requests/{request_id}/approve", response_model=LeaveRequestPublic)
async def approve_leave(
    request_id: uuid.UUID,
    body: LeaveReviewBody,
    session: SessionDep,
    current_user: Annotated[User, Depends(require_roles(Role.admin, Role.manager))],
) -> LeaveRequestPublic:
    return await leave_service.approve_leave(session, current_user, request_id, body.note)


@router.post("/requests/{request_id}/reject", response_model=LeaveRequestPublic)
async def reject_leave(
    request_id: uuid.UUID,
    body: LeaveReviewBody,
    session: SessionDep,
    current_user: Annotated[User, Depends(require_roles(Role.admin, Role.manager))],
) -> LeaveRequestPublic:
    return await leave_service.reject_leave(session, current_user, request_id, body.note)
