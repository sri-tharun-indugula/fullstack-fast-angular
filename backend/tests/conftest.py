import os
import tempfile

_docs_dir = tempfile.mkdtemp(prefix="hrms_docs_test_")
os.environ["JWT_SECRET"] = "test-secret-key-with-32-characters-min"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://hrms:hrms@localhost:5432/hrms_test"
os.environ["CORS_ORIGINS"] = "http://localhost:4200"
os.environ["DOCUMENTS_STORAGE_PATH"] = _docs_dir

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import engine, session_factory
from app.main import app
from app.models.audit import AuditLog
from app.models.attendance import AttendanceDay
from app.models.document import HrDocument
from app.models.goal import PerformanceGoal
from app.models.notification import Notification
from app.models.employee import EmployeeProfile
from app.models.leave import LeaveBalance, LeaveRequest, LeaveType
from app.models.organization import Department
from app.models.user import RefreshToken, Role, User
import app.models.audit as _audit_models  # noqa: F401
import app.models.attendance as _attendance_models  # noqa: F401
import app.models.document as _document_models  # noqa: F401
import app.models.goal as _goal_models  # noqa: F401
import app.models.notification as _notification_models  # noqa: F401
import app.models.employee as _employee_models  # noqa: F401
import app.models.leave as _leave_models  # noqa: F401
import app.models.organization as _organization_models  # noqa: F401


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
    async with session_factory() as session:
        await session.execute(delete(RefreshToken))
        await session.execute(delete(AuditLog))
        await session.execute(delete(Notification))
        await session.execute(delete(HrDocument))
        await session.execute(delete(PerformanceGoal))
        await session.execute(delete(AttendanceDay))
        await session.execute(delete(LeaveRequest))
        await session.execute(delete(LeaveBalance))
        await session.execute(delete(LeaveType))
        await session.execute(delete(EmployeeProfile))
        await session.execute(delete(Department))
        await session.execute(delete(User))
        await session.commit()


async def add_user(
    *,
    email: str,
    password: str,
    role: Role,
    full_name: str = "Test User",
    is_active: bool = True,
) -> None:
    async with session_factory() as session:
        session.add(
            User(
                email=email.lower(),
                hashed_password=hash_password(password),
                full_name=full_name,
                role=role,
                is_active=is_active,
            )
        )
        await session.commit()
