from typing import Optional

from sqlalchemy.orm import Session

from app.db.models.user import Usuario
from app.services.analytics_service import AnalyticsService
from app.db.repositories.users import UsersRepository


class AdminService:
    def __init__(self, db: Session):
        self.repo = UsersRepository(db)
        self.analytics = AnalyticsService(db)

    def list_users(self) -> list[Usuario]:
        return self.repo.list_all()

    def delete_user(self, user_id: int) -> bool:
        return self.repo.delete(user_id)

    def set_admin(self, user_id: int, is_admin: bool) -> Optional[Usuario]:
        return self.repo.set_admin(user_id, is_admin)

    def metrics(self, days: int = 120) -> dict:
        return self.analytics.build_dashboard_metrics(days=days)
