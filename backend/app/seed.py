import asyncio
import uuid
from datetime import date
from decimal import Decimal
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import session_factory
from app.models.employee import EmployeeProfile
from app.models.document import DocumentScope, HrDocument
from app.models.goal import GoalStatus, PerformanceGoal
from app.models.leave import LeaveBalance, LeaveType
from app.models.organization import Department
from app.models.user import Role, User


async def _ensure_department(session, code: str, name: str, parent: Department | None = None) -> Department:
    existing = await session.scalar(select(Department).where(Department.code == code))
    if existing is not None:
        return existing
    department = Department(code=code, name=name, parent_id=parent.id if parent else None)
    session.add(department)
    await session.flush()
    return department


async def _ensure_user(
    session,
    email: str,
    password: str,
    full_name: str,
    role: Role,
) -> User:
    normalized = email.lower()
    user = await session.scalar(select(User).where(User.email == normalized))
    if user is None:
        user = User(
            email=normalized,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
            is_active=True,
        )
        session.add(user)
        await session.flush()
    return user


async def _ensure_profile(
    session,
    user: User,
    *,
    employee_code: str,
    job_title: str,
    department: Department | None,
    manager: User | None,
    work_location: str,
) -> None:
    profile = await session.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == user.id))
    if profile is not None:
        return
    session.add(
        EmployeeProfile(
            user_id=user.id,
            department_id=department.id if department else None,
            manager_user_id=manager.id if manager else None,
            employee_code=employee_code,
            job_title=job_title,
            work_location=work_location,
            joined_on=date(2026, 1, 1),
        )
    )


async def seed() -> None:
    settings = get_settings()
    accounts = (
        (settings.seed_admin_email, settings.seed_admin_password, settings.seed_admin_name, Role.admin),
        (settings.seed_manager_email, settings.seed_manager_password, settings.seed_manager_name, Role.manager),
        (settings.seed_employee_email, settings.seed_employee_password, settings.seed_employee_name, Role.employee),
    )
    missing = [email for email, password, _, _ in accounts if not password]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"Set seed passwords in .env before seeding. Missing for: {joined}")

    async with session_factory() as session:
        hq = await _ensure_department(session, "HQ", "Headquarters")
        engineering = await _ensure_department(session, "ENG", "Engineering", parent=hq)

        admin = await _ensure_user(
            session,
            settings.seed_admin_email,
            settings.seed_admin_password,
            settings.seed_admin_name,
            Role.admin,
        )
        manager = await _ensure_user(
            session,
            settings.seed_manager_email,
            settings.seed_manager_password,
            settings.seed_manager_name,
            Role.manager,
        )
        employee = await _ensure_user(
            session,
            settings.seed_employee_email,
            settings.seed_employee_password,
            settings.seed_employee_name,
            Role.employee,
        )

        await _ensure_profile(
            session,
            admin,
            employee_code="EMP-ADMIN",
            job_title="HR Administrator",
            department=hq,
            manager=None,
            work_location="HQ - Floor 1",
        )
        await _ensure_profile(
            session,
            manager,
            employee_code="EMP-MGR",
            job_title="Engineering Manager",
            department=engineering,
            manager=admin,
            work_location="HQ - Floor 2",
        )
        await _ensure_profile(
            session,
            employee,
            employee_code="EMP-001",
            job_title="Software Engineer",
            department=engineering,
            manager=manager,
            work_location="HQ - Floor 2",
        )

        year = date.today().year
        casual = await _ensure_leave_type(session, "CASUAL", "Casual Leave", Decimal("12"))
        sick = await _ensure_leave_type(session, "SICK", "Sick Leave", Decimal("10"))
        for user in (admin, manager, employee):
            await _ensure_leave_balance(session, user, casual, year, casual.annual_quota)
            await _ensure_leave_balance(session, user, sick, year, sick.annual_quota)

        await _ensure_goal(
            session,
            assignee=employee,
            creator=manager,
            title="Complete onboarding documentation",
            description="Write and publish the team onboarding guide in the internal wiki.",
            due_date=date(year, 12, 31),
        )

        await _ensure_company_document(
            session,
            uploader=admin,
            title="Employee handbook",
            description="Company policies and code of conduct.",
            body=b"HRMS demo handbook. Replace with your real policy PDF.",
        )

        await session.commit()


async def _ensure_company_document(
    session,
    *,
    uploader: User,
    title: str,
    description: str,
    body: bytes,
) -> None:
    existing = await session.scalar(
        select(HrDocument).where(HrDocument.scope == DocumentScope.company, HrDocument.title == title)
    )
    if existing is not None:
        return
    settings = get_settings()
    root = settings.documents_storage_path
    root.mkdir(parents=True, exist_ok=True)
    stored = f"{uuid.uuid4().hex}.txt"
    (root / stored).write_bytes(body)
    session.add(
        HrDocument(
            scope=DocumentScope.company,
            owner_user_id=None,
            uploaded_by_user_id=uploader.id,
            title=title,
            description=description,
            original_filename="handbook.txt",
            stored_filename=stored,
            content_type="text/plain",
            size_bytes=len(body),
        )
    )


async def _ensure_goal(
    session,
    *,
    assignee: User,
    creator: User,
    title: str,
    description: str,
    due_date: date | None,
) -> None:
    existing = await session.scalar(
        select(PerformanceGoal).where(
            PerformanceGoal.assignee_user_id == assignee.id,
            PerformanceGoal.title == title,
        )
    )
    if existing is not None:
        return
    session.add(
        PerformanceGoal(
            assignee_user_id=assignee.id,
            created_by_user_id=creator.id,
            title=title,
            description=description,
            due_date=due_date,
            status=GoalStatus.not_started,
            progress_percent=0,
        )
    )


async def _ensure_leave_type(session, code: str, name: str, annual_quota: Decimal) -> LeaveType:
    existing = await session.scalar(select(LeaveType).where(LeaveType.code == code))
    if existing is not None:
        return existing
    leave_type = LeaveType(code=code, name=name, annual_quota=annual_quota, is_active=True)
    session.add(leave_type)
    await session.flush()
    return leave_type


async def _ensure_leave_balance(
    session,
    user: User,
    leave_type: LeaveType,
    year: int,
    entitled: Decimal,
) -> None:
    existing = await session.scalar(
        select(LeaveBalance).where(
            LeaveBalance.user_id == user.id,
            LeaveBalance.leave_type_id == leave_type.id,
            LeaveBalance.year == year,
        )
    )
    if existing is not None:
        return
    session.add(
        LeaveBalance(
            user_id=user.id,
            leave_type_id=leave_type.id,
            year=year,
            entitled=entitled,
            used=Decimal("0"),
            pending=Decimal("0"),
        )
    )


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
