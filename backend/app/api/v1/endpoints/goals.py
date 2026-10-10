import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, require_roles
from app.models.user import Role, User
from app.schemas.goal import GoalCreate, GoalEmployeeUpdate, GoalManagerUpdate, GoalPublic
from app.services import goals as goals_service

router = APIRouter(prefix="/goals", tags=["goals"])


@router.get("/me", response_model=list[GoalPublic])
async def my_goals(session: SessionDep, current_user: CurrentUser) -> list[GoalPublic]:
    return await goals_service.list_mine(session, current_user)


@router.get("/team", response_model=list[GoalPublic])
async def team_goals(
    session: SessionDep,
    current_user: Annotated[User, Depends(require_roles(Role.admin, Role.manager))],
) -> list[GoalPublic]:
    return await goals_service.list_team(session, current_user)


@router.get("/{goal_id}", response_model=GoalPublic)
async def get_goal(goal_id: uuid.UUID, session: SessionDep, current_user: CurrentUser) -> GoalPublic:
    return await goals_service.get_goal(session, current_user, goal_id)


@router.post("", response_model=GoalPublic, status_code=201)
async def create_goal(
    body: GoalCreate,
    session: SessionDep,
    current_user: Annotated[User, Depends(require_roles(Role.admin, Role.manager))],
) -> GoalPublic:
    return await goals_service.create_goal(session, current_user, body)


@router.patch("/{goal_id}/self", response_model=GoalPublic)
async def update_my_goal(
    goal_id: uuid.UUID,
    body: GoalEmployeeUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> GoalPublic:
    return await goals_service.update_as_employee(session, current_user, goal_id, body)


@router.patch("/{goal_id}", response_model=GoalPublic)
async def manager_update_goal(
    goal_id: uuid.UUID,
    body: GoalManagerUpdate,
    session: SessionDep,
    current_user: Annotated[User, Depends(require_roles(Role.admin, Role.manager))],
) -> GoalPublic:
    return await goals_service.update_as_manager(session, current_user, goal_id, body)
