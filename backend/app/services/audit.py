import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit import AuditAction, AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogList, AuditLogPublic


async def record(
    session: AsyncSession,
    *,
    action: AuditAction,
    summary: str,
    actor_user_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    ip_address: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary,
            ip_address=ip_address,
            metadata_json=metadata,
        )
    )


async def list_logs(
    session: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
    action: AuditAction | None = None,
) -> AuditLogList:
    capped_limit = min(max(limit, 1), 200)
    capped_offset = max(offset, 0)
    filters = []
    if action is not None:
        filters.append(AuditLog.action == action)

    count_query = select(func.count()).select_from(AuditLog)
    if filters:
        count_query = count_query.where(*filters)
    total = int(await session.scalar(count_query) or 0)

    query = select(AuditLog).options(selectinload(AuditLog.actor)).order_by(AuditLog.created_at.desc())
    if filters:
        query = query.where(*filters)
    result = await session.execute(query.limit(capped_limit).offset(capped_offset))
    items: list[AuditLogPublic] = []
    for row in result.scalars().all():
        actor_email = row.actor.email if getattr(row, "actor", None) is not None else None
        items.append(
            AuditLogPublic(
                id=row.id,
                actor_user_id=row.actor_user_id,
                actor_email=actor_email,
                action=row.action,
                entity_type=row.entity_type,
                entity_id=row.entity_id,
                summary=row.summary,
                ip_address=row.ip_address,
                metadata_json=row.metadata_json,
                created_at=row.created_at,
            )
        )
    return AuditLogList(items=items, total=total, limit=capped_limit, offset=capped_offset)
