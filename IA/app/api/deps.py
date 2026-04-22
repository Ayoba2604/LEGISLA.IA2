from typing import Optional

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.models.user import Usuario
from app.db.session import get_db
from app.services.auth_service import AuthService, decode_session_token


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_current_user_optional(
    db: Session = Depends(get_db),
    legisla_session: Optional[str] = Cookie(None, alias=settings.SESSION_COOKIE_NAME),
) -> Optional[Usuario]:
    if not legisla_session:
        return None
    data = decode_session_token(legisla_session)
    if not data:
        return None
    return AuthService(db).get_user_by_id(data["uid"])


def get_current_user(
    user: Optional[Usuario] = Depends(get_current_user_optional),
) -> Usuario:
    if not user:
        raise HTTPException(status_code=401, detail="Nao autenticado.")
    return user


def require_admin(
    user: Usuario = Depends(get_current_user),
) -> Usuario:
    if not user.admin:
        raise HTTPException(status_code=403, detail="Acesso negado. Permissao de administrador necessaria.")
    return user
