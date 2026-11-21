import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from .config import get_settings

password_hash = PasswordHash.recommended()
ALGORITHMS = ["HS256"]


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str | None) -> bool:
    if not hashed:
        password_hash.verify(password, password_hash.hash(secrets.token_urlsafe(32)))
        return False
    return password_hash.verify(password, hashed)


def issue_access_token(user_id: uuid.UUID) -> tuple[str, int]:
    settings = get_settings()
    now = datetime.now(UTC)
    expires_in = settings.access_token_minutes * 60
    claims = {
        "sub": str(user_id),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
        "iss": settings.issuer,
        "aud": settings.audience,
    }
    return jwt.encode(claims, settings.secret_key.get_secret_value(), algorithm="HS256"), expires_in


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    claims = jwt.decode(
        token,
        settings.secret_key.get_secret_value(),
        algorithms=ALGORITHMS,
        issuer=settings.issuer,
        audience=settings.audience,
        options={"require": ["sub", "type", "iat", "exp", "iss", "aud"]},
    )
    if claims.get("type") != "access":
        raise jwt.InvalidTokenError("invalid token type")
    return claims


def new_refresh_token() -> tuple[str, str]:
    raw = secrets.token_urlsafe(48)
    return raw, hashlib.sha256(raw.encode()).hexdigest()


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
