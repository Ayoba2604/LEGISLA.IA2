from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.user import Usuario


class UsersRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> Optional[Usuario]:
        stmt = select(Usuario).where(Usuario.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, user_id: int) -> Optional[Usuario]:
        stmt = select(Usuario).where(Usuario.id_usuario == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, nome: str, email: str, senha_hash: str) -> Usuario:
        user = Usuario(nome=nome, email=email, senha=senha_hash, foto_url=None, admin=False)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def list_all(self) -> list[Usuario]:
        stmt = select(Usuario).order_by(Usuario.id_usuario)
        return list(self.db.execute(stmt).scalars().all())

    def update(self, user_id: int, **fields) -> Optional[Usuario]:
        user = self.get_by_id(user_id)
        if not user:
            return None
        for key, value in fields.items():
            setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user_id: int) -> bool:
        user = self.get_by_id(user_id)
        if not user:
            return False
        self.db.delete(user)
        self.db.commit()
        return True

    def set_admin(self, user_id: int, is_admin: bool) -> Optional[Usuario]:
        return self.update(user_id, admin=is_admin)

    def update_profile(self, user_id: int, nome: str, foto_url: str | None) -> Optional[Usuario]:
        return self.update(user_id, nome=nome, foto_url=foto_url)
