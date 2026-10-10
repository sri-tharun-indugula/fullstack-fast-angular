import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, require_roles
from app.models.user import Role, User
from app.schemas.employee import (
    EmployeeAdminUpdate,
    EmployeeCreate,
    EmployeePublic,
    EmployeeSelfUpdate,
)
from app.models.audit import AuditAction
from app.services import audit as audit_service
from app.services import employee as employee_service

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/me", response_model=EmployeePublic)
async def get_my_profile(session: SessionDep, current_user: CurrentUser) -> EmployeePublic:
    return await employee_service.get_employee_public(session, current_user, current_user.id)


@router.patch("/me", response_model=EmployeePublic)
async def update_my_profile(
    body: EmployeeSelfUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> EmployeePublic:
    return await employee_service.update_self(session, current_user, body)


@router.get("", response_model=list[EmployeePublic])
async def list_employees(session: SessionDep, current_user: CurrentUser) -> list[EmployeePublic]:
    return await employee_service.list_employees(session, current_user)


@router.get("/{user_id}", response_model=EmployeePublic)
async def get_employee(user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser) -> EmployeePublic:
    return await employee_service.get_employee_public(session, current_user, user_id)


@router.post("", response_model=EmployeePublic, status_code=201)
async def create_employee(
    body: EmployeeCreate,
    session: SessionDep,
    current_user: Annotated[User, Depends(require_roles(Role.admin))],
) -> EmployeePublic:
    created = await employee_service.create_employee(session, body)
    await audit_service.record(
        session,
        action=AuditAction.employee_created,
        summary=f"Created employee {created.full_name} ({created.employee_code})",
        actor_user_id=current_user.id,
        entity_type="employee",
        entity_id=created.user_id,
    )
    return created


@router.patch("/{user_id}", response_model=EmployeePublic)
async def admin_update_employee(
    user_id: uuid.UUID,
    body: EmployeeAdminUpdate,
    session: SessionDep,
    current_user: Annotated[User, Depends(require_roles(Role.admin))],
) -> EmployeePublic:
    updated = await employee_service.admin_update_employee(session, user_id, body)
    await audit_service.record(
        session,
        action=AuditAction.employee_updated,
        summary=f"Updated employee profile for {updated.full_name}",
        actor_user_id=current_user.id,
        entity_type="employee",
        entity_id=updated.user_id,
    )
    return updated
