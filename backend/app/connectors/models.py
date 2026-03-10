from __future__ import annotations

from pydantic import BaseModel, Field


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
    max_records: int = Field(default=25, ge=1, le=500)
    only_with_ementa: bool = True


class DataJudQuerySpec(BaseModel):
    enabled: bool = False
    name: str
    endpoint: str
    tribunal: str | None = None
    ramo_direito: str | None = None
    tema: str | None = None
    max_records: int = Field(default=50, ge=1, le=500)
    payload: dict = Field(default_factory=dict)
    extra_headers: dict[str, str] = Field(default_factory=dict)


class OfficialCorpusRegistry(BaseModel):
    snapshot_root: str = "backend/data/corpus_snapshots/official"
    manifest_output_path: str = "backend/data/bootstrap/corpus_manifest.official.json"
    planalto_legislation: list[PlanaltoLegislationSpec] = Field(default_factory=list)
    stj_open_data: list[StjOpenDataSpec] = Field(default_factory=list)
    datajud_queries: list[DataJudQuerySpec] = Field(default_factory=list)


class OfficialCorpusBuildReport(BaseModel):
    registry_path: str
    manifest_path: str
    snapshot_root: str
    connectors_run: list[str] = Field(default_factory=list)
    collected_sources: int = 0
    failed_sources: int = 0
    warnings: list[str] = Field(default_factory=list)

