import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.employee import EmployeeProfile
from app.models.goal import GoalStatus, PerformanceGoal
from app.models.user import Role, User
from app.models.audit import AuditAction
from app.models.notification import NotificationKind
from app.services import audit as audit_service
from app.schemas.goal import GoalCreate, GoalEmployeeUpdate, GoalManagerUpdate, GoalPublic
from app.services import notifications as notifications_service


def _to_public(goal: PerformanceGoal) -> GoalPublic:
    return GoalPublic(
        id=goal.id,
        assignee_user_id=goal.assignee_user_id,
        assignee_name=goal.assignee.full_name,
        created_by_user_id=goal.created_by_user_id,
        title=goal.title,
        description=goal.description,
        due_date=goal.due_date,
        status=goal.status,
        progress_percent=goal.progress_percent,
        manager_note=goal.manager_note,
        created_at=goal.created_at,
        updated_at=goal.updated_at,
    )


async def _load_goal(session: AsyncSession, goal_id: uuid.UUID) -> PerformanceGoal | None:
    result = await session.execute(
        select(PerformanceGoal)
        .where(PerformanceGoal.id == goal_id)
        .options(selectinload(PerformanceGoal.assignee), selectinload(PerformanceGoal.created_by))
    )
    return result.scalar_one_or_none()


def _can_view(viewer: User, goal: PerformanceGoal, profile: EmployeeProfile | None) -> bool:
    if viewer.role == Role.admin:
        return True
    if goal.assignee_user_id == viewer.id:
        return True
    if viewer.role == Role.manager and profile is not None and profile.manager_user_id == viewer.id:
        return True
    return False


async def _can_manage_assignee(session: AsyncSession, viewer: User, assignee_user_id: uuid.UUID) -> bool:
    if viewer.role == Role.admin:
        return True
    if viewer.role != Role.manager:
        return False
    profile = await session.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == assignee_user_id))
    return profile is not None and profile.manager_user_id == viewer.id


async def list_mine(session: AsyncSession, user: User) -> list[GoalPublic]:
    result = await session.execute(
        select(PerformanceGoal)
        .where(PerformanceGoal.assignee_user_id == user.id)
        .options(selectinload(PerformanceGoal.assignee), selectinload(PerformanceGoal.created_by))
        .order_by(PerformanceGoal.due_date.asc().nulls_last(), PerformanceGoal.created_at.desc())
    )
    return [_to_public(item) for item in result.scalars().all()]


async def list_team(session: AsyncSession, viewer: User) -> list[GoalPublic]:
    if viewer.role == Role.employee:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    query = select(PerformanceGoal).options(
        selectinload(PerformanceGoal.assignee),
        selectinload(PerformanceGoal.created_by),
    )
    if viewer.role == Role.manager:
        reports = select(EmployeeProfile.user_id).where(EmployeeProfile.manager_user_id == viewer.id)
        query = query.where(PerformanceGoal.assignee_user_id.in_(reports))
    result = await session.execute(query.order_by(PerformanceGoal.created_at.desc()))
    return [_to_public(item) for item in result.scalars().all()]


async def get_goal(session: AsyncSession, viewer: User, goal_id: uuid.UUID) -> GoalPublic:
    goal = await _load_goal(session, goal_id)
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    profile = await session.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == goal.assignee_user_id))
    if not _can_view(viewer, goal, profile):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return _to_public(goal)


async def create_goal(session: AsyncSession, viewer: User, body: GoalCreate) -> GoalPublic:
    if viewer.role not in {Role.admin, Role.manager}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if not await _can_manage_assignee(session, viewer, body.assignee_user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    assignee = await session.get(User, body.assignee_user_id)
    if assignee is None or not assignee.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee not found")
    goal = PerformanceGoal(
        assignee_user_id=body.assignee_user_id,
        created_by_user_id=viewer.id,
        title=body.title.strip(),
        description=body.description.strip(),
        due_date=body.due_date,
        status=GoalStatus.not_started,
        progress_percent=0,
    )
    session.add(goal)
    await session.flush()
    loaded = await _load_goal(session, goal.id)
    assert loaded is not None
    if body.assignee_user_id != viewer.id:
        await notifications_service.create_notification(
            session,
            user_id=body.assignee_user_id,
            kind=NotificationKind.goal_assigned,
            title="New performance goal",
            body=loaded.title,
            entity_type="goal",
            entity_id=loaded.id,
        )
    await audit_service.record(
        session,
        action=AuditAction.goal_created,
        summary=f'{viewer.full_name} assigned goal "{loaded.title}"',
        actor_user_id=viewer.id,
        entity_type="goal",
        entity_id=loaded.id,
    )
    return _to_public(loaded)


async def update_as_employee(session: AsyncSession, viewer: User, goal_id: uuid.UUID, body: GoalEmployeeUpdate) -> GoalPublic:
    goal = await _load_goal(session, goal_id)
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    if goal.assignee_user_id != viewer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if body.status is not None:
        goal.status = body.status
    if body.progress_percent is not None:
        goal.progress_percent = body.progress_percent
        if goal.status == GoalStatus.not_started and body.progress_percent > 0:
            goal.status = GoalStatus.in_progress
        if body.progress_percent == 100 and goal.status != GoalStatus.cancelled:
            goal.status = GoalStatus.completed
    await session.flush()
    reloaded = await _load_goal(session, goal_id)
    assert reloaded is not None
    return _to_public(reloaded)


async def update_as_manager(
    session: AsyncSession,
    viewer: User,
    goal_id: uuid.UUID,
    body: GoalManagerUpdate,
) -> GoalPublic:
    goal = await _load_goal(session, goal_id)
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    profile = await session.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == goal.assignee_user_id))
    if viewer.role != Role.admin and not (
        viewer.role == Role.manager and profile is not None and profile.manager_user_id == viewer.id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if body.title is not None:
        goal.title = body.title.strip()
    if body.description is not None:
        goal.description = body.description.strip()
    if "due_date" in body.model_fields_set:
        goal.due_date = body.due_date
    if body.status is not None:
        goal.status = body.status
    if body.progress_percent is not None:
        goal.progress_percent = body.progress_percent
    if body.manager_note is not None:
        goal.manager_note = body.manager_note or None
    await session.flush()
    reloaded = await _load_goal(session, goal_id)
    assert reloaded is not None
    return _to_public(reloaded)
