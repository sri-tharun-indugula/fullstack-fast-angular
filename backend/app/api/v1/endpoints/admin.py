from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import SessionDep, require_roles
from app.models.audit import AuditAction
from app.models.user import Role, User
from app.schemas.audit import AuditLogList
from app.schemas.auth import PingResponse
from app.services import audit as audit_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ping", response_model=PingResponse)
async def admin_ping(
    current_user: Annotated[User, Depends(require_roles(Role.admin))],
) -> PingResponse:
    return PingResponse(role=current_user.role)


@router.get("/audit-logs", response_model=AuditLogList)
async def list_audit_logs(
    session: SessionDep,
    _: Annotated[User, Depends(require_roles(Role.admin))],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    action: AuditAction | None = None,
) -> AuditLogList:
    return await audit_service.list_logs(session, limit=limit, offset=offset, action=action)
