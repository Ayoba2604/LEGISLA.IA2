from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models.user import Usuario
from app.db.session import get_db
from app.schemas.auth import UserResponse
from app.services.admin_service import AdminService
from app.api.deps import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    return AdminService(db)


@router.get("/users", response_model=list[UserResponse])
def list_users(
    _admin: Usuario = Depends(require_admin),
    svc: AdminService = Depends(get_admin_service),
):
    return svc.list_users()


@router.get("/metrics")
def get_metrics(
    days: int = 120,
    _admin: Usuario = Depends(require_admin),
    svc: AdminService = Depends(get_admin_service),
):
    safe_days = max(7, min(days, 365))
    return svc.metrics(days=safe_days)


@router.patch("/users/{user_id}/role")
def update_role(
    user_id: int,
    admin: bool,
    current_admin: Usuario = Depends(require_admin),
    svc: AdminService = Depends(get_admin_service),
):
    user = svc.set_admin(user_id, admin)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado.")

    svc.analytics.record_event(
        tipo="admin_action",
        rota="/admin",
        detalhe=f"{current_admin.nome} alterou o perfil admin de {user.nome} para {bool(user.admin)}",
        user_id=current_admin.id_usuario,
    )
    return {"ok": True, "usuario": user.nome, "admin": bool(user.admin)}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_admin: Usuario = Depends(require_admin),
    svc: AdminService = Depends(get_admin_service),
):
    target_user = next((entry for entry in svc.list_users() if entry.id_usuario == user_id), None)
    ok = svc.delete_user(user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado.")

    svc.analytics.record_event(
        tipo="admin_action",
        rota="/admin",
        detalhe=f"{current_admin.nome} removeu {target_user.nome if target_user else 'um usuario'}",
        user_id=current_admin.id_usuario,
    )
    return {"ok": True}
