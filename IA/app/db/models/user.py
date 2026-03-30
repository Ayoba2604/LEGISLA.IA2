from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    senha = Column(String(255), nullable=False)
    foto_url = Column(Text, nullable=True)
    admin = Column(Boolean, nullable=False, default=False)
    criado_em = Column(DateTime, server_default=func.now(), nullable=False)


class EventoSistema(Base):
    __tablename__ = "eventos_sistema"

    id_evento = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    tipo = Column(String(50), nullable=False, index=True)
    rota = Column(String(255), nullable=True)
    detalhe = Column(Text, nullable=True)
    user_id = Column(BigInteger().with_variant(Integer, "sqlite"), nullable=True, index=True)
    criado_em = Column(DateTime, server_default=func.now(), nullable=False, index=True)
