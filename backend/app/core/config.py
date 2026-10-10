from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://hrms:hrms@localhost:5432/hrms"
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    cors_origins: str = "http://localhost:4200"
    refresh_cookie_name: str = "refresh_token"
    refresh_cookie_secure: bool = False
    refresh_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    refresh_cookie_path: str = "/api/v1/auth"
    seed_admin_email: str = "admin@example.com"
    seed_admin_password: str = ""
    seed_admin_name: str = "System Admin"
    seed_manager_email: str = "manager@example.com"
    seed_manager_password: str = ""
    seed_manager_name: str = "Team Manager"
    seed_employee_email: str = "employee@example.com"
    seed_employee_password: str = ""
    seed_employee_name: str = "Alex Employee"
    documents_storage_path: Path = _REPO_ROOT / "data" / "documents"
    document_max_bytes: int = 5 * 1024 * 1024
    app_env: Literal["development", "production"] = "development"
    auth_rate_limit_per_minute: int = 30

    @field_validator("cors_origins")
    @classmethod
    def cors_must_be_explicit(cls, value: str) -> str:
        origins = [part.strip() for part in value.split(",") if part.strip()]
        if not origins or "*" in origins:
            raise ValueError("CORS_ORIGINS must list explicit origins")
        return ",".join(origins)

    @computed_field
    @property
    def cors_origin_list(self) -> list[str]:
        return [part.strip() for part in self.cors_origins.split(",") if part.strip()]

    @computed_field
    @property
    def access_token_expire_seconds(self) -> int:
        return self.access_token_expire_minutes * 60

    @computed_field
    @property
    def refresh_cookie_max_age(self) -> int:
        return self.refresh_token_expire_days * 24 * 60 * 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
