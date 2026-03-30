import logging

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.settings import settings
from app.db.models.user import Base

logger = logging.getLogger(__name__)


def _build_engine():
    url = settings.database_url

    if settings.DB_DRIVER != "sqlite":
        try:
            eng = create_engine(url, pool_pre_ping=True)
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Conectado ao banco: %s", settings.DB_DRIVER)
            return eng
        except Exception as exc:
            logger.warning("Falha ao conectar no %s (%s). Usando SQLite local.", settings.DB_DRIVER, exc)
            url = f"sqlite:///{settings.DB_NAME}.db"

    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    eng = create_engine(url, connect_args=connect_args)
    logger.info("Usando banco SQLite: %s", url)
    return eng


engine = _build_engine()
Base.metadata.create_all(bind=engine)


def _ensure_runtime_schema() -> None:
    inspector = inspect(engine)

    try:
        tables = set(inspector.get_table_names())
    except Exception as exc:
        logger.warning("Nao foi possivel inspecionar o schema atual: %s", exc)
        return

    if "usuarios" in tables:
        user_columns = {column["name"] for column in inspector.get_columns("usuarios")}
        if "foto_url" not in user_columns:
            try:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE usuarios ADD COLUMN foto_url TEXT NULL"))
                logger.info("Coluna foto_url adicionada a tabela usuarios.")
            except Exception as exc:
                logger.warning("Falha ao adicionar coluna foto_url: %s", exc)


_ensure_runtime_schema()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
