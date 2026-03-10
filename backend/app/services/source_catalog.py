from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from backend.app.config.settings import settings
from backend.app.core.enums import SourceAuthority, SourceType
from backend.app.core.text import stable_id
from backend.app.ingestion.chunkers import chunk_source
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.models.domain import SourceMetadata, SourceRecord
from backend.app.services.model_runtime import EmbeddingService

if TYPE_CHECKING:
    from backend.app.repositories.persistence import PersistenceService

logger = logging.getLogger(__name__)


class SourceCatalog:
    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        persistence: "PersistenceService | None" = None,
    ) -> None:
        self.embedding_service = embedding_service or EmbeddingService()
        self.persistence = persistence
        self.sources: dict[str, SourceRecord] = {}
        self.chunks = {}

    def load_bootstrap_sources(self) -> None:
        if self.sources:
            return

        manifest_loaded = self._load_manifest_if_present(settings.bootstrap_manifest_path)
        if not manifest_loaded and settings.enable_legacy_bootstrap_fallback:
            self._load_legacy_seed_file(settings.legacy_data_dir / "base_juridica.json", SourceType.LEGACY_SEED, "consulta")
            self._load_legacy_seed_file(settings.legacy_data_dir / "situacoes.json", SourceType.SITUATION, "situacao")
            self._load_legacy_seed_file(settings.legacy_data_dir / "contratos.json", SourceType.CONTRACT, "contrato")

        logger.info(
            "Bootstrap sources loaded",
            extra={
                "extra_payload": {
                    "sources": len(self.sources),
                    "chunks": len(self.chunks),
                    "manifest_loaded": manifest_loaded,
                }
            },
        )

    def add_source(self, source: SourceRecord, chunks: list, *, persist: bool = True) -> None:
        self.sources[source.source_id] = source
        embeddings = self.embedding_service.embed_documents([chunk.search_text for chunk in chunks]) if chunks else []
        for chunk, embedding in zip(chunks, embeddings):
            if not chunk.embedding:
                chunk.embedding = embedding
            self.chunks[chunk.chunk_id] = chunk
        if persist and self.persistence and self.persistence.enabled:
            self.persistence.sync_source_bundle(source, chunks)

    def list_chunks(self) -> list:
        return list(self.chunks.values())

    def remove_source(self, source_id: str) -> int:
        self.sources.pop(source_id, None)
        removed_chunk_ids = [chunk_id for chunk_id, chunk in self.chunks.items() if chunk.source_id == source_id]
        for chunk_id in removed_chunk_ids:
            self.chunks.pop(chunk_id, None)
        return len(removed_chunk_ids)

    def _load_manifest_if_present(self, manifest_path: Path) -> bool:
        if not manifest_path.exists():
            return False

        pipeline = IngestionPipeline()
        report = pipeline.ingest_manifest(
            manifest_path=manifest_path,
            catalog=self,
            persist=settings.persist_bootstrap_to_db,
        )
        logger.info(
            "Bootstrap manifest imported",
            extra={
                "extra_payload": {
                    "manifest_path": str(manifest_path),
                    "sources": report.imported_sources,
                    "chunks": report.imported_chunks,
                    "warnings": report.warnings,
                }
            },
        )
        return report.imported_sources > 0

    def _load_legacy_seed_file(self, path: Path, source_type: SourceType, theme_label: str) -> None:
        if not path.exists():
            logger.warning("Legacy seed file not found", extra={"extra_payload": {"path": str(path)}})
            return

        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data:
            title = item.get("titulo") or item.get("descricao") or f"Seed {item.get('id')}"
            description = item.get("descricao", "")
            analysis = item.get("analise", "")
            raw_text = "\n".join(value for value in [description, analysis] if value).strip()
            source_id = stable_id(str(path), str(item.get("id")), title)
            source = SourceRecord(
                source_id=source_id,
                document_id=stable_id("document", source_id),
                version_id=stable_id("version", source_id, raw_text),
                title=title,
                source_type=source_type,
                authority=SourceAuthority.SECONDARY,
                is_official=False,
                is_primary=False,
                description=description,
                raw_text=raw_text,
                hierarchy=["legacy", theme_label],
                metadata=SourceMetadata(
                    tema=title,
                    metadata_extra={
                        "legacy_id": item.get("id"),
                        "legacy_origin_file": path.name,
                        "legacy_type": item.get("tipo"),
                    },
                ),
            )
            chunks = chunk_source(source)
            self.add_source(source, chunks, persist=settings.persist_bootstrap_to_db)
