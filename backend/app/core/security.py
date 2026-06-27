"""Parola hashleme ve JWT (access + refresh) üretimi/doğrulaması."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import bcrypt
import jwt

from app.core.config import settings

TokenType = Literal["access", "refresh"]

# bcrypt parolada en fazla 72 bayt dikkate alır; uzun parolalar sessizce kırpılır.
_BCRYPT_MAX_BYTES = 72


def _truncate(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_truncate(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_truncate(password), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _create_token(
    *,
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, **extra_claims: Any) -> str:
    return _create_token(
        subject=subject,
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        extra_claims=extra_claims,
    )


def create_refresh_token(subject: str, **extra_claims: Any) -> str:
    return _create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        extra_claims=extra_claims,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Tokenı doğrular ve payload döner. Geçersizse jwt.PyJWTError fırlatır."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
