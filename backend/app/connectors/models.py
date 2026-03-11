from __future__ import annotations

from pydantic import BaseModel, Field

from backend.app.core.enums import SourceType


class PlanaltoLegislationSpec(BaseModel):
    enabled: bool = True
    title: str
    url: str
    numero_norma: str
    tipo_norma: str
    ramo_direito: str | None = None
    tema: str | None = None
    vigencia: str = "vigente"
    hierarchy: list[str] = Field(default_factory=lambda: ["federal"])


class StjOpenDataSpec(BaseModel):
    enabled: bool = True
    package_name: str
    title: str | None = None
    ramo_direito: str | None = None
    tema: str | None = None
    orgao_julgador_contains: str | None = None
    relator_contains: str | None = None
    numero_processo_contains: str | None = None
    required_terms: list[str] = Field(default_factory=list)
    max_records: int = Field(default=25, ge=1, le=500)
    only_with_ementa: bool = True


class DataJudQuerySpec(BaseModel):
    enabled: bool = False
    name: str
    endpoint: str
    tribunal: str | None = None
    ramo_direito: str | None = None
    tema: str | None = None
    orgao_julgador_contains: str | None = None
    relator_contains: str | None = None
    numero_processo_contains: str | None = None
    required_terms: list[str] = Field(default_factory=list)
    updated_since_days: int | None = Field(default=None, ge=1, le=3650)
    max_records: int = Field(default=50, ge=1, le=500)
    payload: dict = Field(default_factory=dict)
    extra_headers: dict[str, str] = Field(default_factory=dict)


class OfficialSumulaSpec(BaseModel):
    enabled: bool = True
    title: str
    tribunal: str
    url: str
    fallback_urls: list[str] = Field(default_factory=list)
    source_type: SourceType = SourceType.SUMULA
    ramo_direito: str | None = None
    tema: str | None = None
    mime_type: str | None = None
    hierarchy: list[str] = Field(default_factory=list)
    max_entries: int = Field(default=500, ge=1, le=5000)


class OfficialCorpusRegistry(BaseModel):
    snapshot_root: str = "backend/data/corpus_snapshots/official"
    manifest_output_path: str = "backend/data/bootstrap/corpus_manifest.official.json"
    planalto_legislation: list[PlanaltoLegislationSpec] = Field(default_factory=list)
    stj_open_data: list[StjOpenDataSpec] = Field(default_factory=list)
    official_sumulas: list[OfficialSumulaSpec] = Field(default_factory=list)
    datajud_queries: list[DataJudQuerySpec] = Field(default_factory=list)


class OfficialCorpusBuildReport(BaseModel):
    registry_path: str
    manifest_path: str
    snapshot_root: str
    connectors_run: list[str] = Field(default_factory=list)
    collected_sources: int = 0
    failed_sources: int = 0
    warnings: list[str] = Field(default_factory=list)
