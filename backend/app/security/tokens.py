from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from pydantic import BaseModel, Field


class TokenValidationError(ValueError):
    pass


class AuthenticatedUser(BaseModel):
    user_id: str
    email: str | None = None
    admin: bool = False
    session_id: str | None = None
    issued_at: int = Field(default_factory=lambda: int(time.time()))
    expires_at: int


def create_user_token(user: AuthenticatedUser, secret: str) -> str:
    payload = user.model_dump(mode="json")
    encoded_payload = _b64url_encode(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    signature = hmac.new(secret.encode("utf-8"), encoded_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{encoded_payload}.{signature}"


def decode_user_token(token: str, secret: str, *, now_ts: int | None = None) -> AuthenticatedUser:
    try:
        encoded_payload, signature = token.split(".", 1)
    except ValueError as exc:
        raise TokenValidationError("Malformed token.") from exc

    expected_signature = hmac.new(secret.encode("utf-8"), encoded_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        raise TokenValidationError("Invalid signature.")

    try:
        payload = json.loads(_b64url_decode(encoded_payload))
    except Exception as exc:
        raise TokenValidationError("Invalid token payload.") from exc

    user = AuthenticatedUser.model_validate(payload)
    now_ts = now_ts or int(time.time())
    if user.expires_at <= now_ts:
        raise TokenValidationError("Token expired.")
    return user


def _b64url_encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).decode("utf-8").rstrip("=")


def _b64url_decode(payload: str) -> str:
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode((payload + padding).encode("utf-8")).decode("utf-8")
