from fastapi import APIRouter, Depends, Response

from app.core.settings import settings
from app.db.models.user import Usuario
from app.schemas.auth import (
    ProfileUpdateRequest,
    AuthStatusResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthService, create_session_token
from app.api.deps import get_auth_service, get_current_user, get_current_user_optional
from app.db.session import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_analytics_service(db = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


def _set_session_cookie(response: Response, user: Usuario) -> None:
    token = create_session_token(user)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=settings.APP_ENV != "development",
    )


@router.post("/register")
def register(
    body: RegisterRequest,
    response: Response,
    svc: AuthService = Depends(get_auth_service),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    ok, erro, user = svc.register(body.nome, body.email, body.senha)
    if not ok:
        return {"ok": False, "erro": erro}

    _set_session_cookie(response, user)
    analytics.record_event(tipo="register", rota="/cadastro", detalhe="Conta criada", user_id=user.id_usuario)
    return {"ok": True, "usuario": user.nome, "admin": bool(user.admin)}


@router.post("/login")
def login(
    body: LoginRequest,
    response: Response,
    svc: AuthService = Depends(get_auth_service),
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    ok, erro, user = svc.login(body.email, body.senha)
    if not ok:
        return {"ok": False, "erro": erro}

    _set_session_cookie(response, user)
    analytics.record_event(tipo="login", rota="/login", detalhe="Login realizado", user_id=user.id_usuario)
    return {"ok": True, "usuario": user.nome, "admin": bool(user.admin)}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=settings.SESSION_COOKIE_NAME)
    return {"ok": True}


@router.get("/me")
def me(user: Usuario | None = Depends(get_current_user_optional)) -> AuthStatusResponse:
    if not user:
        return AuthStatusResponse(ok=True, logado=False)
    return AuthStatusResponse(
        ok=True,
        logado=True,
        usuario=user.nome,
        email=user.email,
        foto_url=user.foto_url,
        admin=bool(user.admin),
        id_usuario=user.id_usuario,
    )


@router.patch("/profile")
def update_profile(
    body: ProfileUpdateRequest,
    user: Usuario = Depends(get_current_user),
    svc: AuthService = Depends(get_auth_service),
):
    ok, erro, updated_user = svc.update_profile(user.id_usuario, body.nome, body.foto_url)
    if not ok or not updated_user:
        return {"ok": False, "erro": erro or "Nao foi possivel atualizar o perfil."}

    return {
        "ok": True,
        "usuario": updated_user.nome,
        "email": updated_user.email,
        "foto_url": updated_user.foto_url,
        "admin": bool(updated_user.admin),
        "id_usuario": updated_user.id_usuario,
    }
