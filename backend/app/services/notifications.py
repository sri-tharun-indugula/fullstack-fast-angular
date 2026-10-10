import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationKind
from app.models.user import User
from app.schemas.notification import NotificationPublic, UnreadCountPublic


async def create_notification(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    kind: NotificationKind,
    title: str,
    body: str,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
) -> None:
    session.add(
        Notification(
            user_id=user_id,
            kind=kind,
            title=title,
            body=body,
            entity_type=entity_type,
            entity_id=entity_id,
        )
    )


async def list_mine(session: AsyncSession, user: User, unread_only: bool = False) -> list[NotificationPublic]:
    query = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        query = query.where(Notification.read_at.is_(None))
    result = await session.execute(query.order_by(Notification.created_at.desc()).limit(100))
    return [NotificationPublic.model_validate(item) for item in result.scalars().all()]


async def unread_count(session: AsyncSession, user: User) -> UnreadCountPublic:
    count = await session.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user.id, Notification.read_at.is_(None))
    )
    return UnreadCountPublic(count=int(count or 0))


async def mark_read(session: AsyncSession, user: User, notification_id: uuid.UUID) -> NotificationPublic:
    notification = await session.get(Notification, notification_id)
    if notification is None or notification.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if notification.read_at is None:
        notification.read_at = datetime.now(UTC)
        await session.flush()
    return NotificationPublic.model_validate(notification)


async def mark_all_read(session: AsyncSession, user: User) -> None:
    now = datetime.now(UTC)
    result = await session.execute(
        select(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None))
    )
    for item in result.scalars().all():
        item.read_at = now
    await session.flush()
