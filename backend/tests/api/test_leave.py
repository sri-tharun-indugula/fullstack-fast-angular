from datetime import date, timedelta
from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy import select

from app.db.session import session_factory
from app.models.employee import EmployeeProfile
from app.models.leave import LeaveBalance, LeaveType
from app.models.organization import Department
from app.models.user import Role, User
from tests.conftest import add_user

PASSWORD = "test-password-1"


async def _login(client: AsyncClient, email: str) -> str:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    return response.json()["access_token"]


async def _setup_team() -> tuple[str, str]:
    await add_user(email="manager@example.com", password=PASSWORD, role=Role.manager, full_name="Manager")
    await add_user(email="worker@example.com", password=PASSWORD, role=Role.employee, full_name="Worker")
    async with session_factory() as session:
        dept = Department(code="ENG", name="Engineering")
        session.add(dept)
        await session.flush()
        manager = await session.scalar(select(User).where(User.email == "manager@example.com"))
        worker = await session.scalar(select(User).where(User.email == "worker@example.com"))
        session.add(
            EmployeeProfile(
                user_id=manager.id,
                department_id=dept.id,
                employee_code="MGR-1",
                job_title="Manager",
            )
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
        leave_type = LeaveType(code="CASUAL", name="Casual", annual_quota=Decimal("12"), is_active=True)
        session.add(leave_type)
        await session.flush()
        year = date.today().year
        session.add(
            LeaveBalance(
                user_id=worker.id,
                leave_type_id=leave_type.id,
                year=year,
                entitled=Decimal("12"),
            )
        )
        await session.commit()
        return str(leave_type.id), str(worker.id)


async def test_apply_approve_and_balance(client: AsyncClient) -> None:
    leave_type_id, _ = await _setup_team()
    worker_token = await _login(client, "worker@example.com")
    manager_token = await _login(client, "manager@example.com")

    start = date.today() + timedelta(days=7)
    end = start + timedelta(days=1)
    created = await client.post(
        "/api/v1/leave/requests",
        json={
            "leave_type_id": leave_type_id,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "reason": "Family event",
        },
        headers={"Authorization": f"Bearer {worker_token}"},
    )
    assert created.status_code == 201
    request_id = created.json()["id"]
    assert created.json()["status"] == "pending"
    assert Decimal(created.json()["days"]) == Decimal("2")

    balances = await client.get(
        "/api/v1/leave/balances/me",
        headers={"Authorization": f"Bearer {worker_token}"},
    )
    assert balances.status_code == 200
    casual = balances.json()[0]
    assert Decimal(casual["pending"]) == Decimal("2")
    assert Decimal(casual["available"]) == Decimal("10")

    inbox = await client.get("/api/v1/leave/requests/inbox", headers={"Authorization": f"Bearer {manager_token}"})
    assert inbox.status_code == 200
    assert len(inbox.json()) == 1

    approved = await client.post(
        f"/api/v1/leave/requests/{request_id}/approve",
        json={"note": "Approved"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    balances_after = await client.get(
        "/api/v1/leave/balances/me",
        headers={"Authorization": f"Bearer {worker_token}"},
    )
    assert Decimal(balances_after.json()[0]["used"]) == Decimal("2")
    assert Decimal(balances_after.json()[0]["pending"]) == Decimal("0")


async def test_cancel_pending_request(client: AsyncClient) -> None:
    leave_type_id, _ = await _setup_team()
    worker_token = await _login(client, "worker@example.com")
    start = date.today() + timedelta(days=10)
    created = await client.post(
        "/api/v1/leave/requests",
        json={
            "leave_type_id": leave_type_id,
            "start_date": start.isoformat(),
            "end_date": start.isoformat(),
            "reason": "Changed plans",
        },
        headers={"Authorization": f"Bearer {worker_token}"},
    )
    request_id = created.json()["id"]
    cancelled = await client.post(
        f"/api/v1/leave/requests/{request_id}/cancel",
        headers={"Authorization": f"Bearer {worker_token}"},
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
