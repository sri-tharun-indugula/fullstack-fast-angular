import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings
from app.models.user import Role

_password_hash = PasswordHash.recommended()


class TokenError(Exception):
    """Raised when a JWT cannot be decoded or has the wrong type."""


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return _password_hash.verify(password, hashed_password)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _encode(payload: dict[str, Any]) -> str:
    settings = get_settings()
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    if isinstance(token, bytes):
        return token.decode("utf-8")
    return token


def create_access_token(user_id: uuid.UUID, role: Role) -> str:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    return _encode(
        {
            "sub": str(user_id),
            "role": role.value,
            "type": "access",
            "jti": str(uuid.uuid4()),
            "exp": expires_at,
        }
    )


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, datetime]:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    token = _encode(
        {
            "sub": str(user_id),
            "type": "refresh",
            "jti": str(uuid.uuid4()),
            "exp": expires_at,
        }
    )
    return token, expires_at


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:
        raise TokenError("Token invalid") from exc
    return payload
