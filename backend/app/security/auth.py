from __future__ import annotations

from fastapi import Header, HTTPException, status

from backend.app.config.settings import settings
from backend.app.security.tokens import AuthenticatedUser, TokenValidationError, decode_user_token


def require_admin_token(x_admin_token: str | None = Header(default=None)) -> None:
    if not settings.admin_token or settings.admin_token == "change-me":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Token administrativo nao configurado.",
        )
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token administrativo invalido.")


def get_optional_authenticated_user(
    x_legisla_user_token: str | None = Header(default=None, alias="X-Legisla-User-Token"),
) -> AuthenticatedUser | None:
    if not x_legisla_user_token:
        if settings.require_chat_auth:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticacao obrigatoria.")
        return None

    if not settings.internal_service_secret or settings.internal_service_secret == "change-me-internal":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Segredo interno de autenticacao nao configurado.",
        )

    try:
        return decode_user_token(x_legisla_user_token, settings.internal_service_secret)
    except TokenValidationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def require_authenticated_user(
    x_legisla_user_token: str | None = Header(default=None, alias="X-Legisla-User-Token"),
) -> AuthenticatedUser:
    if not x_legisla_user_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticacao obrigatoria.")
    user = get_optional_authenticated_user(x_legisla_user_token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticacao obrigatoria.")
    return user
