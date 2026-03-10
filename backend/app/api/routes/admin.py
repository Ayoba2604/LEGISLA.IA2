from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request

from backend.app.config.settings import settings
from backend.app.observability.metrics import metrics
from backend.app.schemas.admin import (
    AdminOverview,
    CleanupExpiredUploadsReport,
    CleanupExpiredUploadsRequest,
    DatabaseStatus,
    IngestionJobSummary,
    RetrievalLogSummary,
    SyncStateSummary,
    UploadSummary,
)
from backend.app.schemas.ingestion import ManifestIngestionReport, ManifestIngestionRequest
from backend.app.security.auth import require_admin_token

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin_token)],
)


@router.get("/overview", response_model=AdminOverview)
def admin_overview(request: Request):
    persistence = getattr(request.app.state, "persistence", None)
    chat_service = getattr(request.app.state, "chat_service", None)
    database = DatabaseStatus.model_validate(
        persistence.database_status() if persistence else {"enabled": False, "connected": False, "pgvector_ready": False}
    )
    return AdminOverview(
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        retrieval_backend=settings.retrieval_backend,
        llm_backend=chat_service.llm_service.active_backend if chat_service else "unknown",
        embedding_backend=request.app.state.embedding_service.active_backend
        if getattr(request.app.state, "embedding_service", None)
        else "unknown",
        reranker_backend=request.app.state.reranker_service.active_backend
        if getattr(request.app.state, "reranker_service", None)
        else "unknown",
        manifest_path=str(settings.bootstrap_manifest_path),
        manifest_present=settings.bootstrap_manifest_path.exists(),
        database=database,
        metrics=metrics.snapshot(),
    )


@router.get("/metrics")
def admin_metrics():
    return metrics.snapshot()


@router.get("/retrieval-logs", response_model=list[RetrievalLogSummary])
def retrieval_logs(
    request: Request,
    limit: int = Query(default=50, ge=1, le=500),
    conversation_id: str | None = None,
    owner_user_id: str | None = None,
):
    persistence = request.app.state.persistence
    return [RetrievalLogSummary.model_validate(item) for item in persistence.list_recent_retrievals(limit=limit, conversation_id=conversation_id, owner_user_id=owner_user_id)]


@router.get("/ingestion/jobs", response_model=list[IngestionJobSummary])
def ingestion_jobs(request: Request, limit: int = Query(default=20, ge=1, le=200), status: str | None = None):
    persistence = request.app.state.persistence
    return [IngestionJobSummary.model_validate(item) for item in persistence.list_ingestion_jobs(limit=limit, status=status)]


@router.get("/ingestion/sync-state", response_model=list[SyncStateSummary])
def ingestion_sync_state(request: Request, limit: int = Query(default=50, ge=1, le=500), status: str | None = None):
    persistence = request.app.state.persistence
    return [SyncStateSummary.model_validate(item) for item in persistence.list_sync_states(limit=limit, status=status)]


@router.get("/uploads", response_model=list[UploadSummary])
def uploads(
    request: Request,
    limit: int = Query(default=50, ge=1, le=500),
    owner_user_id: str | None = None,
    include_deleted: bool = False,
):
    persistence = request.app.state.persistence
    return [
        UploadSummary.model_validate(item)
        for item in persistence.list_uploads(limit=limit, owner_user_id=owner_user_id, include_deleted=include_deleted)
    ]


@router.post("/maintenance/cleanup-uploads", response_model=CleanupExpiredUploadsReport)
def cleanup_uploads(
    request: Request,
    payload: CleanupExpiredUploadsRequest | None = None,
):
    payload = payload or CleanupExpiredUploadsRequest()
    return request.app.state.maintenance_service.cleanup_expired_uploads(
        catalog=request.app.state.catalog,
        limit=payload.limit,
        hard_delete=payload.hard_delete,
    )


@router.post("/maintenance/sync-manifest", response_model=ManifestIngestionReport)
def sync_manifest(
    request: Request,
    payload: ManifestIngestionRequest | None = None,
):
    payload = payload or ManifestIngestionRequest()
    manifest_path = Path(payload.manifest_path) if payload.manifest_path else settings.bootstrap_manifest_path
    return request.app.state.maintenance_service.sync_manifest(
        catalog=request.app.state.catalog,
        manifest_path=manifest_path,
        persist=payload.persist,
        source_types=payload.source_types,
    )

