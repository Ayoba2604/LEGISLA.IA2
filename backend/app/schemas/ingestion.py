from __future__ import annotations

from pydantic import BaseModel, Field

from backend.app.core.enums import SourceAuthority, SourceType
from backend.app.models.domain import SourceMetadata


class IngestionPreview(BaseModel):
    source_id: str
    chunk_count: int
    detected_source_type: str
    detected_prompt_injection: bool
    warnings: list[str] = Field(default_factory=list)


class LegacyMigrationReport(BaseModel):
    migrated_sources: int
    migrated_chunks: int
    warnings: list[str] = Field(default_factory=list)


class ManifestSourceSpec(BaseModel):
    title: str
    source_type: SourceType
    authority: SourceAuthority = SourceAuthority.PRIMARY
    description: str = ""
    path: str | None = None
    url: str | None = None
    mime_type: str | None = None
    is_official: bool = False
    is_primary: bool = False
    hierarchy: list[str] = Field(default_factory=list)
    metadata: SourceMetadata = Field(default_factory=SourceMetadata)


class ManifestIngestionRequest(BaseModel):
    manifest_path: str | None = None
    persist: bool = True
    source_types: list[SourceType] = Field(default_factory=list)


class ManifestIngestionReport(BaseModel):
    job_id: int | None = None
    imported_sources: int
    imported_chunks: int
    skipped_sources: int = 0
    failed_sources: int = 0
    source_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
