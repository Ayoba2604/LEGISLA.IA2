from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from backend.app.config.settings import settings
from backend.app.core.enums import SourceType
from backend.app.schemas.ingestion import (
    IngestionPreview,
    LegacyMigrationReport,
    ManifestIngestionReport,
    ManifestIngestionRequest,
)
from backend.app.security.auth import require_admin_token, require_authenticated_user
from backend.app.security.tokens import AuthenticatedUser
from backend.app.security.uploads import validate_upload

router = APIRouter(tags=["ingestion"])


@router.post("/api/v1/ingestion/upload", response_model=IngestionPreview)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    user: AuthenticatedUser = Depends(require_authenticated_user),
):
    payload = await validate_upload(file)
    source, chunks, warnings, injection_detected = request.app.state.ingestion_pipeline.ingest_upload(
        filename=file.filename or "upload.bin",
        mime_type=file.content_type or "application/octet-stream",
        payload=payload,
        source_type=SourceType.USER_DOCUMENT,
        metadata={
            "owner_user_id": user.user_id,
            "owner_email": user.email,
            "retention_expires_at": (
                datetime.utcnow() + timedelta(days=settings.user_upload_retention_days)
            ).isoformat(),
        },
    )
    request.app.state.catalog.add_source(source, chunks)
    if getattr(request.app.state, "persistence", None):
        request.app.state.persistence.record_upload(
            conversation_id=None,
            filename=file.filename or "upload.bin",
            mime_type=file.content_type or "application/octet-stream",
            file_size=len(payload),
            source_id=source.source_id,
            owner_user_id=user.user_id,
            retention_expires_at=datetime.utcnow() + timedelta(days=settings.user_upload_retention_days),
        )
    return IngestionPreview(
        source_id=source.source_id,
        chunk_count=len(chunks),
        detected_source_type=source.source_type.value,
        detected_prompt_injection=injection_detected,
        warnings=warnings,
    )


@router.post(
    "/api/v1/ingestion/manifest",
    response_model=ManifestIngestionReport,
    dependencies=[Depends(require_admin_token)],
)
def import_manifest(request: Request, payload: ManifestIngestionRequest | None = None):
    payload = payload or ManifestIngestionRequest()
    manifest_path = Path(payload.manifest_path) if payload.manifest_path else settings.bootstrap_manifest_path
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail=f"Manifesto nao encontrado: {manifest_path}")
    return request.app.state.ingestion_pipeline.ingest_manifest(
        manifest_path=manifest_path,
        catalog=request.app.state.catalog,
        persist=payload.persist,
        source_types=payload.source_types,
    )


@router.post(
    "/api/v1/ingestion/legacy-migration",
    response_model=LegacyMigrationReport,
    dependencies=[Depends(require_admin_token)],
)
def migrate_legacy_data(request: Request):
    before_sources = len(request.app.state.catalog.sources)
    before_chunks = len(request.app.state.catalog.chunks)
    request.app.state.catalog.load_bootstrap_sources()
    return LegacyMigrationReport(
        migrated_sources=len(request.app.state.catalog.sources) - before_sources,
        migrated_chunks=len(request.app.state.catalog.chunks) - before_chunks,
        warnings=["Migracao usa seeds legadas como dados de demonstracao, nao como base oficial."],
    )
