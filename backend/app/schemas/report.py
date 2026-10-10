import uuid

from pydantic import BaseModel


class DepartmentHeadcount(BaseModel):
    department_id: uuid.UUID | None
    department_name: str
    employee_count: int


class ReportsOverview(BaseModel):
    total_employees: int
    headcount_by_department: list[DepartmentHeadcount]
    pending_leave_requests: int
    checked_in_today: int


class TeamReportsOverview(BaseModel):
    direct_reports: int
    pending_leave_requests: int
    checked_in_today: int
