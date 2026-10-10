from httpx import AsyncClient
from sqlalchemy import select

from app.db.session import session_factory
from app.models.employee import EmployeeProfile
from app.models.organization import Department
from app.models.user import Role, User
from tests.conftest import add_user

PASSWORD = "test-password-1"


async def _login(client: AsyncClient, email: str) -> str:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    return response.json()["access_token"]


async def _setup_worker_and_manager() -> None:
    await add_user(email="manager@example.com", password=PASSWORD, role=Role.manager)
    await add_user(email="worker@example.com", password=PASSWORD, role=Role.employee)
    async with session_factory() as session:
        dept = Department(code="ENG", name="Engineering")
        session.add(dept)
        await session.flush()
        manager = await session.scalar(select(User).where(User.email == "manager@example.com"))
        worker = await session.scalar(select(User).where(User.email == "worker@example.com"))
        session.add(
            EmployeeProfile(user_id=manager.id, department_id=dept.id, employee_code="MGR-1", job_title="Manager")
        )
        session.add(
            EmployeeProfile(
                user_id=worker.id,
                department_id=dept.id,
                manager_user_id=manager.id,
                employee_code="EMP-1",
                job_title="Engineer",
            )
        )
        await session.commit()


async def test_check_in_out_and_team_view(client: AsyncClient) -> None:
    await _setup_worker_and_manager()
    worker_token = await _login(client, "worker@example.com")
    manager_token = await _login(client, "manager@example.com")

    empty = await client.get("/api/v1/attendance/today", headers={"Authorization": f"Bearer {worker_token}"})
    assert empty.status_code == 200
    assert empty.json() is None

    check_in = await client.post("/api/v1/attendance/check-in", headers={"Authorization": f"Bearer {worker_token}"})
    assert check_in.status_code == 201

    duplicate = await client.post("/api/v1/attendance/check-in", headers={"Authorization": f"Bearer {worker_token}"})
    assert duplicate.status_code == 409

    team_before = await client.get("/api/v1/attendance/team", headers={"Authorization": f"Bearer {manager_token}"})
    assert team_before.status_code == 200
    assert team_before.json()[0]["check_in_at"] is not None
    assert team_before.json()[0]["check_out_at"] is None

    check_out = await client.post("/api/v1/attendance/check-out", headers={"Authorization": f"Bearer {worker_token}"})
    assert check_out.status_code == 200
    assert check_out.json()["check_out_at"] is not None

    history = await client.get("/api/v1/attendance/me", headers={"Authorization": f"Bearer {worker_token}"})
    assert history.status_code == 200
    assert len(history.json()) >= 1
