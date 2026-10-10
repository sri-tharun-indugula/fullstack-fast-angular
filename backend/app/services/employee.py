import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.employee import EmployeeProfile
from app.models.organization import Department
from app.models.user import Role, User
from app.schemas.employee import EmployeeAdminUpdate, EmployeeCreate, EmployeePublic, EmployeeSelfUpdate


def _to_public(profile: EmployeeProfile) -> EmployeePublic:
    user = profile.user
    manager_name = profile.manager.full_name if profile.manager is not None else None
    department = profile.department
    return EmployeePublic(
        id=profile.id,
        user_id=profile.user_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        employee_code=profile.employee_code,
        job_title=profile.job_title,
        phone=profile.phone,
        work_location=profile.work_location,
        joined_on=profile.joined_on,
        department=department,
        manager_user_id=profile.manager_user_id,
        manager_full_name=manager_name,
    )


async def _load_profile(session: AsyncSession, profile_id: uuid.UUID) -> EmployeeProfile | None:
    result = await session.execute(
        select(EmployeeProfile)
        .where(EmployeeProfile.id == profile_id)
        .options(
            selectinload(EmployeeProfile.user),
            selectinload(EmployeeProfile.department),
            selectinload(EmployeeProfile.manager),
        )
    )
    return result.scalar_one_or_none()


async def get_profile_by_user_id(session: AsyncSession, user_id: uuid.UUID) -> EmployeeProfile | None:
    result = await session.execute(
        select(EmployeeProfile)
        .where(EmployeeProfile.user_id == user_id)
        .options(
            selectinload(EmployeeProfile.user),
            selectinload(EmployeeProfile.department),
            selectinload(EmployeeProfile.manager),
        )
    )
    return result.scalar_one_or_none()


def can_view_employee(viewer: User, target: EmployeeProfile) -> bool:
    if viewer.role == Role.admin:
        return True
    if viewer.id == target.user_id:
        return True
    if viewer.role == Role.manager and target.manager_user_id == viewer.id:
        return True
    return False


async def get_employee_public(session: AsyncSession, viewer: User, user_id: uuid.UUID) -> EmployeePublic:
    profile = await get_profile_by_user_id(session, user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found")
    if not can_view_employee(viewer, profile):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return _to_public(profile)


async def list_employees(session: AsyncSession, viewer: User) -> list[EmployeePublic]:
    query = (
        select(EmployeeProfile)
        .options(
            selectinload(EmployeeProfile.user),
            selectinload(EmployeeProfile.department),
            selectinload(EmployeeProfile.manager),
        )
        .order_by(EmployeeProfile.employee_code)
    )
    if viewer.role == Role.admin:
        result = await session.execute(query)
    elif viewer.role == Role.manager:
        result = await session.execute(query.where(EmployeeProfile.manager_user_id == viewer.id))
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return [_to_public(item) for item in result.scalars().all()]


async def update_self(session: AsyncSession, viewer: User, body: EmployeeSelfUpdate) -> EmployeePublic:
    profile = await get_profile_by_user_id(session, viewer.id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found")
    if body.phone is not None:
        profile.phone = body.phone or None
    if body.work_location is not None:
        profile.work_location = body.work_location or None
    await session.flush()
    return _to_public(profile)


async def create_employee(session: AsyncSession, body: EmployeeCreate) -> EmployeePublic:
    user = await session.get(User, body.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    existing = await get_profile_by_user_id(session, body.user_id)
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee profile already exists")
    code = body.employee_code.upper()
    taken = await session.scalar(select(EmployeeProfile).where(EmployeeProfile.employee_code == code))
    if taken is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee code already exists")
    if body.department_id is not None and await session.get(Department, body.department_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    if body.manager_user_id is not None and await session.get(User, body.manager_user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manager not found")
    profile = EmployeeProfile(
        user_id=body.user_id,
        department_id=body.department_id,
        manager_user_id=body.manager_user_id,
        employee_code=code,
        job_title=body.job_title.strip(),
        phone=body.phone,
        work_location=body.work_location,
        joined_on=body.joined_on,
    )
    session.add(profile)
    await session.flush()
    loaded = await _load_profile(session, profile.id)
    assert loaded is not None
    return _to_public(loaded)


async def admin_update_employee(
    session: AsyncSession,
    user_id: uuid.UUID,
    body: EmployeeAdminUpdate,
) -> EmployeePublic:
    profile = await get_profile_by_user_id(session, user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found")
    if "department_id" in body.model_fields_set:
        if body.department_id is not None and await session.get(Department, body.department_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
        profile.department_id = body.department_id
    if "manager_user_id" in body.model_fields_set:
        if body.manager_user_id is not None and await session.get(User, body.manager_user_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Manager not found")
        profile.manager_user_id = body.manager_user_id
    if body.job_title is not None:
        profile.job_title = body.job_title.strip()
    if body.employee_code is not None:
        code = body.employee_code.upper()
        taken = await session.scalar(
            select(EmployeeProfile).where(
                EmployeeProfile.employee_code == code,
                EmployeeProfile.id != profile.id,
            )
        )
        if taken is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee code already exists")
        profile.employee_code = code
    if body.phone is not None:
        profile.phone = body.phone or None
    if body.work_location is not None:
        profile.work_location = body.work_location or None
    if body.joined_on is not None:
        profile.joined_on = body.joined_on
    await session.flush()
    return _to_public(profile)
