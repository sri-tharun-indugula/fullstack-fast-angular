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


async def _setup_users() -> None:
    await add_user(email="admin@example.com", password=PASSWORD, role=Role.admin)
    await add_user(email="employee@example.com", password=PASSWORD, role=Role.employee)
    async with session_factory() as session:
        dept = Department(code="HQ", name="HQ")
        session.add(dept)
        await session.flush()
        admin = await session.scalar(select(User).where(User.email == "admin@example.com"))
        employee = await session.scalar(select(User).where(User.email == "employee@example.com"))
        session.add(
            EmployeeProfile(user_id=admin.id, department_id=dept.id, employee_code="A-1", job_title="Admin")
        )
        session.add(
            EmployeeProfile(
                user_id=employee.id,
                department_id=dept.id,
                employee_code="E-1",
                job_title="Staff",
            )
        )
        await session.commit()


async def test_company_document_visible_to_employee(client: AsyncClient) -> None:
    await _setup_users()
    admin_token = await _login(client, "admin@example.com")
    employee_token = await _login(client, "employee@example.com")

    upload = await client.post(
        "/api/v1/documents",
        data={"title": "Handbook", "scope": "company", "description": "Policies"},
        files={"file": ("handbook.txt", b"Welcome to HRMS", "text/plain")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert upload.status_code == 201
    doc_id = upload.json()["id"]

    listed = await client.get("/api/v1/documents/me", headers={"Authorization": f"Bearer {employee_token}"})
    assert listed.status_code == 200
    assert any(item["id"] == doc_id for item in listed.json())

    download = await client.get(
        f"/api/v1/documents/{doc_id}/content",
        headers={"Authorization": f"Bearer {employee_token}"},
    )
    assert download.status_code == 200
    assert download.content == b"Welcome to HRMS"
