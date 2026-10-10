from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, SessionDep, require_roles
from app.models.user import Role, User
from app.schemas.attendance import AttendancePublic, TeamAttendanceRow
from app.services import attendance as attendance_service

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.get("/today", response_model=AttendancePublic | None)
async def today(session: SessionDep, current_user: CurrentUser) -> AttendancePublic | None:
    return await attendance_service.get_today(session, current_user)


@router.post("/check-in", response_model=AttendancePublic, status_code=201)
async def check_in(session: SessionDep, current_user: CurrentUser) -> AttendancePublic:
    return await attendance_service.check_in(session, current_user)


@router.post("/check-out", response_model=AttendancePublic)
async def check_out(session: SessionDep, current_user: CurrentUser) -> AttendancePublic:
    return await attendance_service.check_out(session, current_user)


@router.get("/me", response_model=list[AttendancePublic])
async def my_attendance(
    session: SessionDep,
    current_user: CurrentUser,
    from_date: Annotated[date | None, Query(alias="from")] = None,
    to_date: Annotated[date | None, Query(alias="to")] = None,
) -> list[AttendancePublic]:
    return await attendance_service.list_mine(session, current_user, from_date, to_date)


@router.get("/team", response_model=list[TeamAttendanceRow])
async def team_attendance(
    session: SessionDep,
    current_user: Annotated[User, Depends(require_roles(Role.admin, Role.manager))],
    work_date: Annotated[date | None, Query(alias="date")] = None,
) -> list[TeamAttendanceRow]:
    target = work_date or datetime.now(UTC).date()
    return await attendance_service.team_for_date(session, current_user, target)
