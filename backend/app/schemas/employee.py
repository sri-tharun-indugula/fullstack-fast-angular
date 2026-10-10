import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.department import DepartmentPublic


class EmployeeSelfUpdate(BaseModel):
    phone: str | None = Field(default=None, max_length=32)
    work_location: str | None = Field(default=None, max_length=255)


class EmployeeAdminUpdate(BaseModel):
    department_id: uuid.UUID | None = None
    manager_user_id: uuid.UUID | None = None
    job_title: str | None = Field(default=None, min_length=1, max_length=255)
    employee_code: str | None = Field(default=None, min_length=1, max_length=32, pattern=r"^[A-Z0-9_-]+$")
    phone: str | None = Field(default=None, max_length=32)
    work_location: str | None = Field(default=None, max_length=255)
    joined_on: date | None = None


class EmployeeCreate(BaseModel):
    user_id: uuid.UUID
    department_id: uuid.UUID | None = None
    manager_user_id: uuid.UUID | None = None
    employee_code: str = Field(min_length=1, max_length=32, pattern=r"^[A-Z0-9_-]+$")
    job_title: str = Field(min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    work_location: str | None = Field(default=None, max_length=255)
    joined_on: date | None = None


class EmployeePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    full_name: str
    role: str
    employee_code: str
    job_title: str
    phone: str | None
    work_location: str | None
    joined_on: date | None
    department: DepartmentPublic | None
    manager_user_id: uuid.UUID | None
    manager_full_name: str | None
