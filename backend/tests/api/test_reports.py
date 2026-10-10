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


async def test_admin_reports_overview(client: AsyncClient) -> None:
    await add_user(email="admin@example.com", password=PASSWORD, role=Role.admin)
    async with session_factory() as session:
        dept = Department(code="OPS", name="Operations")
        session.add(dept)
        await session.flush()
        admin = await session.scalar(select(User).where(User.email == "admin@example.com"))
        session.add(
            EmployeeProfile(user_id=admin.id, department_id=dept.id, employee_code="ADM-1", job_title="Admin")
        )
        await session.commit()

    token = await _login(client, "admin@example.com")
    response = await client.get("/api/v1/reports/overview", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_employees"] == 1
    assert len(payload["headcount_by_department"]) == 1
