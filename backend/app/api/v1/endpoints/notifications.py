import uuid

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, SessionDep
from app.schemas.notification import NotificationPublic, UnreadCountPublic
from app.services import notifications as notifications_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/me", response_model=list[NotificationPublic])
async def my_notifications(
    session: SessionDep,
    current_user: CurrentUser,
    unread_only: bool = Query(False),
) -> list[NotificationPublic]:
    return await notifications_service.list_mine(session, current_user, unread_only=unread_only)


@router.get("/unread-count", response_model=UnreadCountPublic)
async def unread_count(session: SessionDep, current_user: CurrentUser) -> UnreadCountPublic:
    return await notifications_service.unread_count(session, current_user)


@router.patch("/{notification_id}/read", response_model=NotificationPublic)
async def mark_read(
    notification_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> NotificationPublic:
    return await notifications_service.mark_read(session, current_user, notification_id)


@router.post("/read-all", status_code=204)
async def mark_all_read(session: SessionDep, current_user: CurrentUser) -> None:
    await notifications_service.mark_all_read(session, current_user)
