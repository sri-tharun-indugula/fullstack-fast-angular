import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class AttendancePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    work_date: date
    check_in_at: datetime
    check_out_at: datetime | None


class TeamAttendanceRow(BaseModel):
    user_id: uuid.UUID
    full_name: str
    employee_code: str | None
    work_date: date
    check_in_at: datetime | None
    check_out_at: datetime | None

