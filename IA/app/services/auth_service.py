import json
import hashlib
import hmac
import time
from typing import Optional

import bcrypt
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.models.user import Usuario
from app.db.repositories.users import UsersRepository


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _sign(payload: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode(), payload.encode(), hashlib.sha256,
    ).hexdigest()


def create_session_token(user: Usuario) -> str:
    data = {
        "uid": user.id_usuario,
        "exp": int(time.time()) + settings.SESSION_MAX_AGE,
    }
    payload = json.dumps(data, separators=(",", ":"))
    sig = _sign(payload)
    return f"{payload}.{sig}"


def decode_session_token(token: str) -> Optional[dict]:
    try:
        payload, sig = token.rsplit(".", 1)
        if not hmac.compare_digest(sig, _sign(payload)):
            return None
        data = json.loads(payload)
        if data.get("exp", 0) < time.time():
            return None
        return data
    except Exception:
        return None


class AuthService:
    def __init__(self, db: Session):
        self.repo = UsersRepository(db)

    def register(self, nome: str, email: str, senha: str) -> tuple[bool, str, Optional[Usuario]]:
        if not nome or not email or not senha:
            return False, "Todos os campos sao obrigatorios.", None

        if len(senha) < 6:
            return False, "A senha deve ter pelo menos 6 caracteres.", None

        existing = self.repo.get_by_email(email)
        if existing:
            return False, "Este email ja esta cadastrado.", None

        hashed = hash_password(senha)
        user = self.repo.create(nome=nome, email=email, senha_hash=hashed)
        return True, "", user

    def login(self, email: str, senha: str) -> tuple[bool, str, Optional[Usuario]]:
        if not email or not senha:
            return False, "Email e senha sao obrigatorios.", None

        user = self.repo.get_by_email(email)
        if not user or not verify_password(senha, user.senha):
            return False, "Email ou senha invalidos.", None

        return True, "", user

    def get_user_by_id(self, user_id: int) -> Optional[Usuario]:
        return self.repo.get_by_id(user_id)

    def update_profile(self, user_id: int, nome: str, foto_url: str | None) -> tuple[bool, str, Optional[Usuario]]:
        nome = (nome or '').strip()
        foto_url = (foto_url or '').strip() or None

        if not nome:
            return False, "O nome nao pode ficar vazio.", None

        if len(nome) > 150:
            return False, "O nome excede o limite permitido.", None

        if foto_url and len(foto_url) > 1_500_000:
            return False, "A imagem selecionada e muito grande.", None

        user = self.repo.update_profile(user_id, nome=nome, foto_url=foto_url)
        if not user:
            return False, "Usuario nao encontrado.", None

        return True, "", user
