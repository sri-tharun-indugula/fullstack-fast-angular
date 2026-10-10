import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate


async def list_departments(session: AsyncSession) -> list[Department]:
    result = await session.execute(select(Department).order_by(Department.name))
    return list(result.scalars().all())


async def create_department(session: AsyncSession, body: DepartmentCreate) -> Department:
    code = body.code.upper()
    existing = await session.scalar(select(Department).where(Department.code == code))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Department code already exists")
    if body.parent_id is not None:
        parent = await session.get(Department, body.parent_id)
        if parent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent department not found")
    department = Department(name=body.name.strip(), code=code, parent_id=body.parent_id)
    session.add(department)
    await session.flush()
    return department


async def update_department(session: AsyncSession, department_id: uuid.UUID, body: DepartmentUpdate) -> Department:
    department = await session.get(Department, department_id)
    if department is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    if body.name is not None:
        department.name = body.name.strip()
    if body.parent_id is not None:
        if body.parent_id == department.id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Department cannot be its own parent")
        parent = await session.get(Department, body.parent_id)
        if parent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent department not found")
        department.parent_id = body.parent_id
    await session.flush()
    return department
