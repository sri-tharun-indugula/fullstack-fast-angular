import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.employee import EmployeeProfile
from app.models.leave import LeaveBalance, LeaveRequest, LeaveStatus, LeaveType
from app.models.user import Role, User
from app.models.audit import AuditAction
from app.models.notification import NotificationKind
from app.services import audit as audit_service
from app.schemas.leave import LeaveBalancePublic, LeaveRequestCreate, LeaveRequestPublic, LeaveTypePublic
from app.services import notifications as notifications_service


def _inclusive_days(start: date, end: date) -> Decimal:
    return Decimal(str((end - start).days + 1))


def _request_public(request: LeaveRequest) -> LeaveRequestPublic:
    return LeaveRequestPublic(
        id=request.id,
        user_id=request.user_id,
        employee_name=request.user.full_name,
        leave_type=LeaveTypePublic.model_validate(request.leave_type),
        start_date=request.start_date,
        end_date=request.end_date,
        days=request.days,
        reason=request.reason,
        status=request.status,
        reviewer_user_id=request.reviewer_user_id,
        reviewed_at=request.reviewed_at,
        reviewer_note=request.reviewer_note,
        created_at=request.created_at,
    )


async def _load_request(session: AsyncSession, request_id: uuid.UUID) -> LeaveRequest | None:
    result = await session.execute(
        select(LeaveRequest)
        .where(LeaveRequest.id == request_id)
        .options(
            selectinload(LeaveRequest.user),
            selectinload(LeaveRequest.leave_type),
            selectinload(LeaveRequest.reviewer),
        )
    )
    return result.scalar_one_or_none()


async def _get_balance(
    session: AsyncSession,
    user_id: uuid.UUID,
    leave_type_id: uuid.UUID,
    year: int,
) -> LeaveBalance | None:
    return await session.scalar(
        select(LeaveBalance).where(
            LeaveBalance.user_id == user_id,
            LeaveBalance.leave_type_id == leave_type_id,
            LeaveBalance.year == year,
        )
    )


async def list_leave_types(session: AsyncSession) -> list[LeaveTypePublic]:
    result = await session.execute(select(LeaveType).where(LeaveType.is_active.is_(True)).order_by(LeaveType.code))
    return [LeaveTypePublic.model_validate(item) for item in result.scalars().all()]


async def list_my_balances(session: AsyncSession, user: User, year: int | None = None) -> list[LeaveBalancePublic]:
    target_year = year or date.today().year
    result = await session.execute(
        select(LeaveBalance)
        .where(LeaveBalance.user_id == user.id, LeaveBalance.year == target_year)
        .options(selectinload(LeaveBalance.leave_type))
        .order_by(LeaveBalance.leave_type_id)
    )
    balances: list[LeaveBalancePublic] = []
    for row in result.scalars().all():
        available = row.entitled - row.used - row.pending
        balances.append(
            LeaveBalancePublic(
                leave_type=LeaveTypePublic.model_validate(row.leave_type),
                year=row.year,
                entitled=row.entitled,
                used=row.used,
                pending=row.pending,
                available=available,
            )
        )
    return balances


async def list_my_requests(session: AsyncSession, user: User) -> list[LeaveRequestPublic]:
    result = await session.execute(
        select(LeaveRequest)
        .where(LeaveRequest.user_id == user.id)
        .options(selectinload(LeaveRequest.user), selectinload(LeaveRequest.leave_type))
        .order_by(LeaveRequest.created_at.desc())
    )
    return [_request_public(item) for item in result.scalars().all()]


async def apply_leave(session: AsyncSession, user: User, body: LeaveRequestCreate) -> LeaveRequestPublic:
    if user.role not in {Role.employee, Role.manager, Role.admin}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    profile = await session.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile required")

    today = date.today()
    if body.start_date < today:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="start_date cannot be in the past")

    leave_type = await session.get(LeaveType, body.leave_type_id)
    if leave_type is None or not leave_type.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave type not found")

    days = _inclusive_days(body.start_date, body.end_date)
    if days <= 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid leave duration")

    year = body.start_date.year
    if body.end_date.year != year:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Leave must stay within one calendar year")

    balance = await _get_balance(session, user.id, body.leave_type_id, year)
    if balance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave balance not found for this year")
    available = balance.entitled - balance.used - balance.pending
    if days > available:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Insufficient leave balance")

    request = LeaveRequest(
        user_id=user.id,
        leave_type_id=body.leave_type_id,
        start_date=body.start_date,
        end_date=body.end_date,
        days=days,
        reason=body.reason.strip(),
        status=LeaveStatus.pending,
    )
    balance.pending += days
    session.add(request)
    await session.flush()
    loaded = await _load_request(session, request.id)
    assert loaded is not None
    if profile.manager_user_id is not None:
        await notifications_service.create_notification(
            session,
            user_id=profile.manager_user_id,
            kind=NotificationKind.leave_submitted,
            title="Leave request pending",
            body=f"{user.full_name} requested {days} day(s) of {leave_type.name}",
            entity_type="leave_request",
            entity_id=loaded.id,
        )
    await audit_service.record(
        session,
        action=AuditAction.leave_applied,
        summary=f"{user.full_name} applied for {days} day(s) leave",
        actor_user_id=user.id,
        entity_type="leave_request",
        entity_id=loaded.id,
    )
    return _request_public(loaded)


async def cancel_leave(session: AsyncSession, user: User, request_id: uuid.UUID) -> LeaveRequestPublic:
    request = await _load_request(session, request_id)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
    if request.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if request.status != LeaveStatus.pending:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Only pending requests can be cancelled")

    balance = await _get_balance(session, user.id, request.leave_type_id, request.start_date.year)
    if balance is not None:
        balance.pending -= request.days
    request.status = LeaveStatus.cancelled
    await session.flush()
    return _request_public(request)


def _can_review(viewer: User, request: LeaveRequest, employee: EmployeeProfile | None) -> bool:
    if viewer.role == Role.admin:
        return True
    if viewer.role == Role.manager and employee is not None and employee.manager_user_id == viewer.id:
        return True
    return False


async def list_inbox(session: AsyncSession, viewer: User) -> list[LeaveRequestPublic]:
    query = (
        select(LeaveRequest)
        .where(LeaveRequest.status == LeaveStatus.pending)
        .options(selectinload(LeaveRequest.user), selectinload(LeaveRequest.leave_type))
        .order_by(LeaveRequest.created_at.asc())
    )
    if viewer.role == Role.admin:
        result = await session.execute(query)
        return [_request_public(item) for item in result.scalars().all()]
    if viewer.role == Role.manager:
        reports = select(EmployeeProfile.user_id).where(EmployeeProfile.manager_user_id == viewer.id)
        result = await session.execute(query.where(LeaveRequest.user_id.in_(reports)))
        return [_request_public(item) for item in result.scalars().all()]
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


async def approve_leave(session: AsyncSession, viewer: User, request_id: uuid.UUID, note: str | None) -> LeaveRequestPublic:
    request = await _load_request(session, request_id)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
    if request.status != LeaveStatus.pending:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Request is not pending")

    employee = await session.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == request.user_id))
    if not _can_review(viewer, request, employee):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    balance = await _get_balance(session, request.user_id, request.leave_type_id, request.start_date.year)
    if balance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave balance not found")
    balance.pending -= request.days
    balance.used += request.days

    request.status = LeaveStatus.approved
    request.reviewer_user_id = viewer.id
    request.reviewed_at = datetime.now(UTC)
    request.reviewer_note = note
    await session.flush()
    await notifications_service.create_notification(
        session,
        user_id=request.user_id,
        kind=NotificationKind.leave_approved,
        title="Leave approved",
        body=f"Your leave from {request.start_date} to {request.end_date} was approved",
        entity_type="leave_request",
        entity_id=request.id,
    )
    await audit_service.record(
        session,
        action=AuditAction.leave_approved,
        summary=f"{viewer.full_name} approved leave request {request.id}",
        actor_user_id=viewer.id,
        entity_type="leave_request",
        entity_id=request.id,
    )
    return _request_public(request)


async def reject_leave(session: AsyncSession, viewer: User, request_id: uuid.UUID, note: str | None) -> LeaveRequestPublic:
    request = await _load_request(session, request_id)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
    if request.status != LeaveStatus.pending:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Request is not pending")

    employee = await session.scalar(select(EmployeeProfile).where(EmployeeProfile.user_id == request.user_id))
    if not _can_review(viewer, request, employee):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    balance = await _get_balance(session, request.user_id, request.leave_type_id, request.start_date.year)
    if balance is not None:
        balance.pending -= request.days

    request.status = LeaveStatus.rejected
    request.reviewer_user_id = viewer.id
    request.reviewed_at = datetime.now(UTC)
    request.reviewer_note = note
    await session.flush()
    await notifications_service.create_notification(
        session,
        user_id=request.user_id,
        kind=NotificationKind.leave_rejected,
        title="Leave rejected",
        body=f"Your leave from {request.start_date} to {request.end_date} was rejected",
        entity_type="leave_request",
        entity_id=request.id,
    )
    await audit_service.record(
        session,
        action=AuditAction.leave_rejected,
        summary=f"{viewer.full_name} rejected leave request {request.id}",
        actor_user_id=viewer.id,
        entity_type="leave_request",
        entity_id=request.id,
    )
    return _request_public(request)
