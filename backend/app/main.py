from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.router import router
from backend.app.config.logging import configure_logging
from backend.app.config.settings import settings
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.repositories.persistence import PersistenceService
from backend.app.security.rate_limit import SimpleRateLimitMiddleware
from backend.app.services.chat_service import ChatService
from backend.app.services.maintenance_service import MaintenanceScheduler, MaintenanceService
from backend.app.services.model_runtime import EmbeddingService
from backend.app.services.reranker_service import RerankerService
from backend.app.services.source_catalog import SourceCatalog

configure_logging(logging.DEBUG if settings.debug else logging.INFO)


def _build_application_state():
    embedding_service = EmbeddingService()
    reranker_service = RerankerService()
    persistence = PersistenceService(embedding_service)
    catalog = SourceCatalog(embedding_service=embedding_service, persistence=persistence)
    catalog.load_bootstrap_sources()
    chat_service = ChatService(
        catalog,
        embedding_service=embedding_service,
        reranker_service=reranker_service,
        persistence=persistence,
    )
    ingestion_pipeline = IngestionPipeline()
    maintenance_service = MaintenanceService(persistence=persistence, ingestion_pipeline=ingestion_pipeline)
    maintenance_scheduler = MaintenanceScheduler(maintenance_service, catalog)
    return {
        "catalog": catalog,
        "chat_service": chat_service,
        "ingestion_pipeline": ingestion_pipeline,
        "persistence": persistence,
        "embedding_service": embedding_service,
        "reranker_service": reranker_service,
        "maintenance_service": maintenance_service,
        "maintenance_scheduler": maintenance_scheduler,
    }


def initialize_app_state(app: FastAPI) -> None:
    if getattr(app.state, "chat_service", None) is not None:
        return
    for key, value in _build_application_state().items():
        setattr(app.state, key, value)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_app_state(app)
    await app.state.maintenance_scheduler.start()
    try:
        yield
    finally:
        await app.state.maintenance_scheduler.stop()


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.add_middleware(SimpleRateLimitMiddleware, requests_per_minute=settings.rate_limit_requests_per_minute)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Admin-Token", "X-Legisla-User-Token"],
)
initialize_app_state(app)
app.include_router(router)


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("backend.app.main:app", host=settings.host, port=settings.port, reload=settings.debug)
