from httpx import AsyncClient

from app.models.user import Role
from tests.conftest import add_user

PASSWORD = "test-password-1"


async def test_login_me_refresh_and_logout(client: AsyncClient) -> None:
    await add_user(email="admin@example.com", password=PASSWORD, role=Role.admin, full_name="Ada Admin")

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": PASSWORD},
    )
    assert login.status_code == 200
    body = login.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 900
    assert body["access_token"]
    assert "refresh_token" in login.cookies

    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "admin@example.com"
    assert me.json()["role"] == "admin"
    assert me.json()["full_name"] == "Ada Admin"

    previous_refresh = login.cookies["refresh_token"]
    refreshed = await client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"] != body["access_token"]
    assert refreshed.cookies["refresh_token"] != previous_refresh

    client.cookies.set("refresh_token", previous_refresh, path="/api/v1/auth")
    reused = await client.post("/api/v1/auth/refresh")
    assert reused.status_code == 401

    fresh_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": PASSWORD},
    )
    assert fresh_login.status_code == 200
    logout = await client.post("/api/v1/auth/logout")
    assert logout.status_code == 204
    after_logout = await client.post("/api/v1/auth/refresh")
    assert after_logout.status_code == 401


async def test_login_rejects_unknown_and_inactive_users(client: AsyncClient) -> None:
    await add_user(email="off@example.com", password=PASSWORD, role=Role.employee, is_active=False)
    unknown = await client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.com", "password": PASSWORD},
    )
    inactive = await client.post(
        "/api/v1/auth/login",
        json={"email": "off@example.com", "password": PASSWORD},
    )
    assert unknown.status_code == 401
    assert inactive.status_code == 401
    assert unknown.json()["detail"] == "Invalid email or password"


async def test_login_validation_error(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/login", json={"email": "not-an-email", "password": ""})
    assert response.status_code == 422


async def test_me_requires_access_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_refresh_requires_cookie(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


async def test_admin_ping_role_gate(client: AsyncClient) -> None:
    await add_user(email="admin@example.com", password=PASSWORD, role=Role.admin)
    await add_user(email="employee@example.com", password=PASSWORD, role=Role.employee)

    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": PASSWORD},
    )
    allowed = await client.get(
        "/api/v1/admin/ping",
        headers={"Authorization": f"Bearer {admin_login.json()['access_token']}"},
    )
    assert allowed.status_code == 200
    assert allowed.json()["role"] == "admin"

    employee_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "employee@example.com", "password": PASSWORD},
    )
    denied = await client.get(
        "/api/v1/admin/ping",
        headers={"Authorization": f"Bearer {employee_login.json()['access_token']}"},
    )
    assert denied.status_code == 403
