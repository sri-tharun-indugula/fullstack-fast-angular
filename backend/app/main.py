import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.middleware.security_headers import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title="HRMS API", version="0.1.0")
    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    if settings.app_env == "production" and not settings.refresh_cookie_secure:
        logger.warning("APP_ENV=production but REFRESH_COOKIE_SECURE is false")
    application.include_router(api_router, prefix="/api/v1")
    return application


app = create_app()
