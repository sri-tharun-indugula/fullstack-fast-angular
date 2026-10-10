from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    attendance,
    auth,
    departments,
    documents,
    employees,
    goals,
    health,
    leave,
    notifications,
    reports,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(departments.router)
api_router.include_router(employees.router)
api_router.include_router(leave.router)
api_router.include_router(attendance.router)
api_router.include_router(goals.router)
api_router.include_router(documents.router)
api_router.include_router(notifications.router)
api_router.include_router(reports.router)
