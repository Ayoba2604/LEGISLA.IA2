from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: str
    senha: str


class RegisterRequest(BaseModel):
    nome: str
    email: EmailStr
    senha: str


class UserResponse(BaseModel):
    id_usuario: int
    nome: str
    email: str
    foto_url: str | None = None
    admin: bool

    model_config = {"from_attributes": True}


class AuthStatusResponse(BaseModel):
    ok: bool
    logado: bool = False
    usuario: str = ""
    email: str = ""
    foto_url: str | None = None
    admin: bool = False
    id_usuario: int | None = None


class ProfileUpdateRequest(BaseModel):
    nome: str
    foto_url: str | None = None


class AnalyticsEventRequest(BaseModel):
    tipo: str
    rota: str | None = None
    detalhe: str | None = None
