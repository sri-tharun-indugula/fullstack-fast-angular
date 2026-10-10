from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.attendance import AttendanceDay
from app.models.employee import EmployeeProfile
from app.models.user import Role, User
from app.schemas.attendance import AttendancePublic, TeamAttendanceRow


def _today() -> date:
    return datetime.now(UTC).date()


def _to_public(record: AttendanceDay) -> AttendancePublic:
    return AttendancePublic.model_validate(record)


async def _require_profile(session: AsyncSession, user: User) -> EmployeeProfile:
    profile = await session.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile required")
    return profile


async def get_today(session: AsyncSession, user: User) -> AttendancePublic | None:
    record = await session.scalar(
        select(AttendanceDay).where(AttendanceDay.user_id == user.id, AttendanceDay.work_date == _today())
    )
    if record is None:
        return None
    return _to_public(record)


async def check_in(session: AsyncSession, user: User) -> AttendancePublic:
    await _require_profile(session, user)
    work_date = _today()
    existing = await session.scalar(
        select(AttendanceDay).where(AttendanceDay.user_id == user.id, AttendanceDay.work_date == work_date)
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already checked in for today")
    now = datetime.now(UTC)
    record = AttendanceDay(user_id=user.id, work_date=work_date, check_in_at=now)
    session.add(record)
    await session.flush()
    return _to_public(record)


async def check_out(session: AsyncSession, user: User) -> AttendancePublic:
    await _require_profile(session, user)
    record = await session.scalar(
        select(AttendanceDay).where(AttendanceDay.user_id == user.id, AttendanceDay.work_date == _today())
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No check-in found for today")
    if record.check_out_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already checked out for today")
    record.check_out_at = datetime.now(UTC)
    await session.flush()
    return _to_public(record)


async def list_mine(
    session: AsyncSession,
    user: User,
    from_date: date | None,
    to_date: date | None,
) -> list[AttendancePublic]:
    end = to_date or _today()
    start = from_date or (end - timedelta(days=30))
    if start > end:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="from_date must be on or before to_date")
    result = await session.execute(
        select(AttendanceDay)
        .where(
            AttendanceDay.user_id == user.id,
            AttendanceDay.work_date >= start,
            AttendanceDay.work_date <= end,
        )
        .order_by(AttendanceDay.work_date.desc())
    )
    return [_to_public(item) for item in result.scalars().all()]


async def team_for_date(session: AsyncSession, viewer: User, work_date: date) -> list[TeamAttendanceRow]:
    if viewer.role == Role.employee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    if viewer.role == Role.admin:
        profiles_result = await session.execute(
            select(EmployeeProfile).options(selectinload(EmployeeProfile.user)).order_by(EmployeeProfile.employee_code)
        )
        profiles = list(profiles_result.scalars().all())
    else:
        profiles_result = await session.execute(
            select(EmployeeProfile)
            .where(EmployeeProfile.manager_user_id == viewer.id)
            .options(selectinload(EmployeeProfile.user))
            .order_by(EmployeeProfile.employee_code)
        )
        profiles = list(profiles_result.scalars().all())

    user_ids = [profile.user_id for profile in profiles]
    if not user_ids:
        return []

    attendance_result = await session.execute(
        select(AttendanceDay).where(AttendanceDay.user_id.in_(user_ids), AttendanceDay.work_date == work_date)
    )
    by_user = {row.user_id: row for row in attendance_result.scalars().all()}

    rows: list[TeamAttendanceRow] = []
    for profile in profiles:
        record = by_user.get(profile.user_id)
        rows.append(
            TeamAttendanceRow(
                user_id=profile.user_id,
                full_name=profile.user.full_name,
                employee_code=profile.employee_code,
                work_date=work_date,
                check_in_at=record.check_in_at if record else None,
                check_out_at=record.check_out_at if record else None,
            )
        )
    return rows
