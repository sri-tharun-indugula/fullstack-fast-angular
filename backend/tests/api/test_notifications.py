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


async def test_goal_assignment_notifies_assignee(client: AsyncClient) -> None:
    await add_user(email="manager@example.com", password=PASSWORD, role=Role.manager)
    await add_user(email="worker@example.com", password=PASSWORD, role=Role.employee)
    async with session_factory() as session:
        dept = Department(code="ENG", name="Engineering")
        session.add(dept)
        await session.flush()
        manager = await session.scalar(select(User).where(User.email == "manager@example.com"))
        worker = await session.scalar(select(User).where(User.email == "worker@example.com"))
        session.add(
            EmployeeProfile(user_id=manager.id, department_id=dept.id, employee_code="M-1", job_title="Manager")
        )
        session.add(
            EmployeeProfile(
                user_id=worker.id,
                department_id=dept.id,
                manager_user_id=manager.id,
                employee_code="W-1",
                job_title="Engineer",
            )
        )
        await session.commit()
        worker_id = str(worker.id)

    manager_token = await _login(client, "manager@example.com")
    worker_token = await _login(client, "worker@example.com")

    created = await client.post(
        "/api/v1/goals",
        json={"assignee_user_id": worker_id, "title": "Ship feature", "description": "MVP"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert created.status_code == 201

    notifications = await client.get(
        "/api/v1/notifications/me",
        headers={"Authorization": f"Bearer {worker_token}"},
    )
    assert notifications.status_code == 200
    items = notifications.json()
    assert len(items) == 1
    assert items[0]["kind"] == "goal_assigned"

    count = await client.get(
        "/api/v1/notifications/unread-count",
        headers={"Authorization": f"Bearer {worker_token}"},
    )
    assert count.json()["count"] == 1

    read = await client.patch(
        f"/api/v1/notifications/{items[0]['id']}/read",
        headers={"Authorization": f"Bearer {worker_token}"},
    )
    assert read.status_code == 200
    assert read.json()["read_at"] is not None
