from httpx import AsyncClient

from app.models.user import Role
from tests.conftest import add_user

PASSWORD = "test-password-1"


async def test_successful_login_writes_audit_log(client: AsyncClient) -> None:
    await add_user(email="auditor@example.com", password=PASSWORD, role=Role.admin)
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "auditor@example.com", "password": PASSWORD},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    logs = await client.get(
        "/api/v1/admin/audit-logs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logs.status_code == 200
    body = logs.json()
    assert body["total"] >= 1
    assert any(item["action"] == "auth.login_success" for item in body["items"])
