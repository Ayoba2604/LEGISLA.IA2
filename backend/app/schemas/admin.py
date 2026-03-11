from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CleanupExpiredUploadsRequest(BaseModel):
    limit: int = Field(default=200, ge=1, le=5000)
    hard_delete: bool = False


class CleanupExpiredUploadsReport(BaseModel):
    processed_uploads: int
    purged_sources: int
    removed_chunks: int
    hard_deleted_uploads: int
    soft_deleted_uploads: int
    source_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DatabaseStatus(BaseModel):
    enabled: bool
    connected: bool
    pgvector_ready: bool
    failed_sync_sources: int = 0
    expired_uploads_pending: int = 0
    running_ingestion_jobs: int = 0
    error: str | None = None


class IngestionJobSummary(BaseModel):
    id: int
    manifest_path: str
    status: str
    source_types: list[str] = Field(default_factory=list)
    imported_sources: int
    imported_chunks: int
    skipped_sources: int
    failed_sources: int
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    finished_at: datetime | None = None


class SyncStateSummary(BaseModel):
    source_key: str
    source_id: str | None = None
    version_id: str | None = None
    last_hash: str | None = None
    status: str
    last_error: str | None = None
    last_synced_at: datetime | None = None


class RetrievalLogSummary(BaseModel):
    id: int
    conversation_id: str | None = None
    owner_user_id: str | None = None
    query_text: str
    intent: str | None = None
    confidence_score: float
    latency_ms: float
    selected_chunk_ids: list[str] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class UploadSummary(BaseModel):
    id: str
    conversation_id: str | None = None
    owner_user_id: str | None = None
    filename: str
    mime_type: str
    file_size: int
    source_id: str | None = None
    retention_expires_at: datetime | None = None
    deleted_at: datetime | None = None
    created_at: datetime | None = None


class OperationalAlert(BaseModel):
    code: str
    severity: str
    message: str
    context: dict[str, Any] = Field(default_factory=dict)


class AdminOverview(BaseModel):
    app: str
    version: str
    environment: str
    retrieval_backend: str
    llm_backend: str
    embedding_backend: str
    reranker_backend: str
    manifest_path: str
    manifest_present: bool
    database: DatabaseStatus
    metrics: dict[str, Any] = Field(default_factory=dict)
    alerts: list[OperationalAlert] = Field(default_factory=list)
