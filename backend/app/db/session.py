from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.config.settings import settings

engine = create_engine(settings.database_url or "postgresql+psycopg://postgres:postgres@localhost:5432/legislaia", future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

