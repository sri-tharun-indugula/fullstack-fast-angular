from datetime import date

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


async def _setup_team() -> None:
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


async def test_manager_assigns_and_employee_updates_progress(client: AsyncClient) -> None:
    await _setup_team()
    manager_token = await _login(client, "manager@example.com")
    worker_token = await _login(client, "worker@example.com")

    async with session_factory() as session:
        worker = await session.scalar(select(User).where(User.email == "worker@example.com"))
        worker_id = str(worker.id)

    created = await client.post(
        "/api/v1/goals",
        json={
            "assignee_user_id": worker_id,
            "title": "Improve test coverage",
            "description": "Raise API test coverage above 80%.",
            "due_date": date(2026, 12, 31).isoformat(),
        },
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert created.status_code == 201
    goal_id = created.json()["id"]

    mine = await client.get("/api/v1/goals/me", headers={"Authorization": f"Bearer {worker_token}"})
    assert mine.status_code == 200
    assert len(mine.json()) == 1

    updated = await client.patch(
        f"/api/v1/goals/{goal_id}/self",
        json={"progress_percent": 50, "status": "in_progress"},
        headers={"Authorization": f"Bearer {worker_token}"},
    )
    assert updated.status_code == 200
    assert updated.json()["progress_percent"] == 50

    team = await client.get("/api/v1/goals/team", headers={"Authorization": f"Bearer {manager_token}"})
    assert team.status_code == 200
    assert team.json()[0]["progress_percent"] == 50
