from typing import Literal

from pydantic import BaseModel, Field

from app.models.user import Role


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = Field(description="Access token lifetime in seconds")


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class PingResponse(BaseModel):
    status: Literal["ok"] = "ok"
    role: Role
