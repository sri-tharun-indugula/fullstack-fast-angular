import uuid

from httpx import AsyncClient
from sqlalchemy import select

from app.db.session import session_factory
from app.models.employee import EmployeeProfile
from app.models.organization import Department
from app.models.user import Role, User
from tests.conftest import add_user

PASSWORD = "test-password-1"


async def _login(client: AsyncClient, email: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": PASSWORD},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


async def _add_department(code: str = "ENG", name: str = "Engineering") -> uuid.UUID:
    async with session_factory() as session:
        existing = await session.scalar(select(Department).where(Department.code == code))
        if existing is not None:
            return existing.id
        department = Department(code=code, name=name)
        session.add(department)
        await session.commit()
        await session.refresh(department)
        return department.id


async def _add_profile(
    email: str,
    role: Role,
    *,
    employee_code: str,
    manager_email: str | None = None,
) -> None:
    await add_user(email=email, password=PASSWORD, role=role, full_name=email.split("@")[0])
    dept_id = await _add_department()
    async with session_factory() as session:
        user = await session.scalar(select(User).where(User.email == email.lower()))
        manager_id = None
        if manager_email:
            manager = await session.scalar(select(User).where(User.email == manager_email.lower()))
            manager_id = manager.id if manager else None
        session.add(
            EmployeeProfile(
                user_id=user.id,
                department_id=dept_id,
                manager_user_id=manager_id,
                employee_code=employee_code,
                job_title="Engineer",
            )
        )
        await session.commit()


async def test_employee_self_service_and_manager_team(client: AsyncClient) -> None:
    await _add_profile("admin@example.com", Role.admin, employee_code="ADM-1")
    await _add_profile("manager@example.com", Role.manager, employee_code="MGR-1", manager_email="admin@example.com")
    await _add_profile("worker@example.com", Role.employee, employee_code="EMP-1", manager_email="manager@example.com")

    worker_token = await _login(client, "worker@example.com")
    me = await client.get("/api/v1/employees/me", headers={"Authorization": f"Bearer {worker_token}"})
    assert me.status_code == 200
    assert me.json()["employee_code"] == "EMP-1"

    patch = await client.patch(
        "/api/v1/employees/me",
        json={"phone": "+1-555-0100"},
        headers={"Authorization": f"Bearer {worker_token}"},
    )
    assert patch.status_code == 200
    assert patch.json()["phone"] == "+1-555-0100"

    manager_token = await _login(client, "manager@example.com")
    team = await client.get("/api/v1/employees", headers={"Authorization": f"Bearer {manager_token}"})
    assert team.status_code == 200
    assert len(team.json()) == 1
    assert team.json()[0]["email"] == "worker@example.com"

    denied = await client.get("/api/v1/employees", headers={"Authorization": f"Bearer {worker_token}"})
    assert denied.status_code == 403


async def test_departments_admin_only(client: AsyncClient) -> None:
    await add_user(email="admin@example.com", password=PASSWORD, role=Role.admin)
    await add_user(email="manager@example.com", password=PASSWORD, role=Role.manager)
    admin_token = await _login(client, "admin@example.com")
    manager_token = await _login(client, "manager@example.com")

    created = await client.post(
        "/api/v1/departments",
        json={"name": "People Ops", "code": "HR"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert created.status_code == 201

    listed = await client.get("/api/v1/departments", headers={"Authorization": f"Bearer {manager_token}"})
    assert listed.status_code == 200
    assert any(item["code"] == "HR" for item in listed.json())

    forbidden = await client.post(
        "/api/v1/departments",
        json={"name": "Finance", "code": "FIN"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert forbidden.status_code == 403
