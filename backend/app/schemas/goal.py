import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.goal import GoalStatus


class GoalCreate(BaseModel):
    assignee_user_id: uuid.UUID
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=4000)
    due_date: date | None = None


class GoalEmployeeUpdate(BaseModel):
    status: GoalStatus | None = None
    progress_percent: int | None = Field(default=None, ge=0, le=100)

    @field_validator("status")
    @classmethod
    def employee_status(cls, value: GoalStatus | None) -> GoalStatus | None:
        if value is not None and value == GoalStatus.cancelled:
            raise ValueError("Employees cannot cancel goals")
        return value


class GoalManagerUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1, max_length=4000)
    due_date: date | None = None
    status: GoalStatus | None = None
    progress_percent: int | None = Field(default=None, ge=0, le=100)
    manager_note: str | None = Field(default=None, max_length=4000)


class GoalPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assignee_user_id: uuid.UUID
    assignee_name: str
    created_by_user_id: uuid.UUID | None
    title: str
    description: str
    due_date: date | None
    status: GoalStatus
    progress_percent: int
    manager_note: str | None
    created_at: datetime
    updated_at: datetime
