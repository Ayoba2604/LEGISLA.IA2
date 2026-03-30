from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional
from app.db.models.user import Usuario
from app.db.session import get_db
from app.schemas.auth import AnalyticsEventRequest
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


@router.post("/events")
def track_event(
    body: AnalyticsEventRequest,
    user: Usuario | None = Depends(get_current_user_optional),
    svc: AnalyticsService = Depends(get_analytics_service),
):
    svc.record_event(
        tipo=body.tipo,
        rota=body.rota,
        detalhe=body.detalhe,
        user_id=user.id_usuario if user else None,
    )
    return {"ok": True}
