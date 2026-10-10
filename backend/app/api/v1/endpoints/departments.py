import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, require_roles
from app.models.user import Role, User
from app.schemas.department import DepartmentCreate, DepartmentPublic, DepartmentUpdate
from app.services import organization as organization_service

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentPublic])
async def list_departments(
    session: SessionDep,
    current_user: Annotated[User, Depends(require_roles(Role.admin, Role.manager))],
) -> list[DepartmentPublic]:
    departments = await organization_service.list_departments(session)
    return [DepartmentPublic.model_validate(item) for item in departments]


@router.post("", response_model=DepartmentPublic, status_code=201)
async def create_department(
    body: DepartmentCreate,
    session: SessionDep,
    _: Annotated[User, Depends(require_roles(Role.admin))],
) -> DepartmentPublic:
    department = await organization_service.create_department(session, body)
    return DepartmentPublic.model_validate(department)


@router.patch("/{department_id}", response_model=DepartmentPublic)
async def update_department(
    department_id: uuid.UUID,
    body: DepartmentUpdate,
    session: SessionDep,
    _: Annotated[User, Depends(require_roles(Role.admin))],
) -> DepartmentPublic:
    department = await organization_service.update_department(session, department_id, body)
    return DepartmentPublic.model_validate(department)
