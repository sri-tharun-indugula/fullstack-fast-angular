import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.leave import LeaveStatus


class LeaveTypePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    annual_quota: Decimal
    is_active: bool


class LeaveBalancePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    leave_type: LeaveTypePublic
    year: int
    entitled: Decimal
    used: Decimal
    pending: Decimal
    available: Decimal


class LeaveRequestCreate(BaseModel):
    leave_type_id: uuid.UUID
    start_date: date
    end_date: date
    reason: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def end_not_before_start(self) -> "LeaveRequestCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class LeaveReviewBody(BaseModel):
    note: str | None = Field(default=None, max_length=2000)


class LeaveRequestPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    employee_name: str
    leave_type: LeaveTypePublic
    start_date: date
    end_date: date
    days: Decimal
    reason: str
    status: LeaveStatus
    reviewer_user_id: uuid.UUID | None
    reviewed_at: datetime | None
    reviewer_note: str | None
    created_at: datetime
