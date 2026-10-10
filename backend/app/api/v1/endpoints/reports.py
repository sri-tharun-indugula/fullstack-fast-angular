from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep, require_roles
from app.models.user import Role, User
from app.schemas.report import ReportsOverview, TeamReportsOverview
from app.services import reports as reports_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/overview", response_model=ReportsOverview)
async def reports_overview(
    session: SessionDep,
    _: Annotated[User, Depends(require_roles(Role.admin))],
) -> ReportsOverview:
    return await reports_service.admin_overview(session)


@router.get("/team", response_model=TeamReportsOverview)
async def team_reports_overview(
    session: SessionDep,
    current_user: Annotated[User, Depends(require_roles(Role.admin, Role.manager))],
) -> TeamReportsOverview:
    return await reports_service.manager_team_overview(session, current_user)
