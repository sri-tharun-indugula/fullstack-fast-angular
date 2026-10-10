from datetime import UTC, date, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceDay
from app.models.employee import EmployeeProfile
from app.models.leave import LeaveRequest, LeaveStatus
from app.models.organization import Department
from app.models.user import Role, User
from app.schemas.report import DepartmentHeadcount, ReportsOverview, TeamReportsOverview


def _utc_today() -> date:
    return datetime.now(UTC).date()


async def admin_overview(session: AsyncSession) -> ReportsOverview:
    total = int(await session.scalar(select(func.count()).select_from(EmployeeProfile)) or 0)

    dept_rows = await session.execute(
        select(Department.id, Department.name, func.count(EmployeeProfile.user_id))
        .select_from(EmployeeProfile)
        .outerjoin(Department, EmployeeProfile.department_id == Department.id)
        .group_by(Department.id, Department.name)
        .order_by(Department.name.nulls_last())
    )
    headcount: list[DepartmentHeadcount] = []
    for dept_id, dept_name, count in dept_rows.all():
        headcount.append(
            DepartmentHeadcount(
                department_id=dept_id,
                department_name=dept_name or "Unassigned",
                employee_count=int(count),
            )
        )

    pending = int(
        await session.scalar(
            select(func.count()).select_from(LeaveRequest).where(LeaveRequest.status == LeaveStatus.pending)
        )
        or 0
    )

    today = _utc_today()
    checked_in = int(
        await session.scalar(
            select(func.count())
            .select_from(AttendanceDay)
            .where(AttendanceDay.work_date == today, AttendanceDay.check_in_at.is_not(None))
        )
        or 0
    )

    return ReportsOverview(
        total_employees=total,
        headcount_by_department=headcount,
        pending_leave_requests=pending,
        checked_in_today=checked_in,
    )


async def manager_team_overview(session: AsyncSession, viewer: User) -> TeamReportsOverview:
    if viewer.role not in {Role.admin, Role.manager}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    if viewer.role == Role.admin:
        direct_reports = int(await session.scalar(select(func.count()).select_from(EmployeeProfile)) or 0)
        report_ids = select(EmployeeProfile.user_id)
    else:
        direct_reports = int(
            await session.scalar(
                select(func.count())
                .select_from(EmployeeProfile)
                .where(EmployeeProfile.manager_user_id == viewer.id)
            )
            or 0
        )
        report_ids = select(EmployeeProfile.user_id).where(EmployeeProfile.manager_user_id == viewer.id)

    pending = int(
        await session.scalar(
            select(func.count())
            .select_from(LeaveRequest)
            .where(LeaveRequest.status == LeaveStatus.pending, LeaveRequest.user_id.in_(report_ids))
        )
        or 0
    )

    today = _utc_today()
    checked_in = int(
        await session.scalar(
            select(func.count())
            .select_from(AttendanceDay)
            .where(
                AttendanceDay.work_date == today,
                AttendanceDay.check_in_at.is_not(None),
                AttendanceDay.user_id.in_(report_ids),
            )
        )
        or 0
    )

    return TeamReportsOverview(
        direct_reports=direct_reports,
        pending_leave_requests=pending,
        checked_in_today=checked_in,
    )
