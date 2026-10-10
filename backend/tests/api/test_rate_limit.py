import os

from httpx import AsyncClient

from app.core.config import get_settings
from app.core.rate_limit import reset_rate_limits

PASSWORD = "wrong-password"


async def test_login_rate_limit_returns_429(client: AsyncClient, monkeypatch) -> None:
    monkeypatch.setenv("AUTH_RATE_LIMIT_PER_MINUTE", "2")
    get_settings.cache_clear()
    reset_rate_limits()

    for _ in range(2):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": PASSWORD},
        )
        assert response.status_code == 401

    blocked = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": PASSWORD},
    )
    assert blocked.status_code == 429

    reset_rate_limits()
    os.environ.pop("AUTH_RATE_LIMIT_PER_MINUTE", None)
    get_settings.cache_clear()
