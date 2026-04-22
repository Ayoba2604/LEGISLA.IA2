from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.user import EventoSistema


class AnalyticsRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_event(
        self,
        *,
        tipo: str,
        rota: str | None = None,
        detalhe: str | None = None,
        user_id: int | None = None,
    ) -> EventoSistema:
        event = EventoSistema(tipo=tipo, rota=rota, detalhe=detalhe, user_id=user_id)
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list_events_since(self, since: datetime) -> list[EventoSistema]:
        stmt = (
            select(EventoSistema)
            .where(EventoSistema.criado_em >= since)
            .order_by(EventoSistema.criado_em.asc())
        )
        return list(self.db.execute(stmt).scalars().all())
