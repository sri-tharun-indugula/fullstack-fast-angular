import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.audit import AuditAction


class AuditLogPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_user_id: uuid.UUID | None
    actor_email: str | None
    action: AuditAction
    entity_type: str | None
    entity_id: uuid.UUID | None
    summary: str
    ip_address: str | None
    metadata_json: dict[str, Any] | None
    created_at: datetime


class AuditLogList(BaseModel):
    items: list[AuditLogPublic]
    total: int
    limit: int
    offset: int
