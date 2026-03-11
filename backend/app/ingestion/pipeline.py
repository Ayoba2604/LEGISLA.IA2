from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.core.enums import SourceAuthority, SourceType
from backend.app.core.text import stable_id
from backend.app.ingestion.chunkers import chunk_source
from backend.app.ingestion.fetchers import fetch_remote_payload, load_local_payload
from backend.app.ingestion.legal_metadata import enrich_source_metadata
from backend.app.ingestion.loaders import load_bytes_as_text
from backend.app.ingestion.normalizers import compute_document_hash
from backend.app.models.domain import ChunkRecord, SourceMetadata, SourceRecord
from backend.app.schemas.ingestion import ManifestIngestionReport, ManifestSourceSpec
from backend.app.security.guardrails import detect_prompt_injection


class IngestionPipeline:
    def ingest_upload(
        self,
        *,
        filename: str,
        mime_type: str,
        payload: bytes,
        source_type: SourceType = SourceType.USER_DOCUMENT,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[SourceRecord, list[ChunkRecord], list[str], bool]:
        metadata_payload = SourceMetadata(
            hash_documento=None,
            metadata_extra=metadata or {},
        )
        return self._build_source_bundle(
            title=filename,
            description=f"Upload do usuario: {filename}",
            filename=filename,
            mime_type=mime_type,
            payload=payload,
            source_type=source_type,
            authority=SourceAuthority.PRIVATE if source_type == SourceType.USER_DOCUMENT else SourceAuthority.SECONDARY,
            is_official=False,
            is_primary=source_type == SourceType.USER_DOCUMENT,
            hierarchy=[],
            metadata=metadata_payload,
        )

    def ingest_manifest(
        self,
        *,
        manifest_path: Path,
        catalog,
        persist: bool = True,
        source_types: list[SourceType] | None = None,
    ) -> ManifestIngestionReport:
        raw_data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        specs = [ManifestSourceSpec.model_validate(item) for item in raw_data]
        allowed_types = {item for item in source_types or []}
        source_ids: list[str] = []
        warnings: list[str] = []
        imported_chunks = 0
        skipped_sources = 0
        failed_sources = 0
        persistence = getattr(catalog, "persistence", None) if persist else None
        job_id = None
        if persistence and persistence.enabled:
            job_id = persistence.start_ingestion_job(
                manifest_path=str(manifest_path),
                source_types=[item.value for item in source_types or []],
            )

        try:
            for spec in specs:
                if allowed_types and spec.source_type not in allowed_types:
                    continue
                source_key = self._source_key(spec)
                try:
                    source, chunks, bundle_warnings, _ = self.ingest_source_spec(spec)
                    if persistence and persistence.enabled:
                        sync_state = persistence.get_sync_state(source_key)
                        if sync_state and sync_state.get("last_hash") == source.metadata.hash_documento:
                            skipped_sources += 1
                            persistence.upsert_sync_state(
                                source_key=source_key,
                                source_id=sync_state.get("source_id"),
                                version_id=sync_state.get("version_id"),
                                last_hash=sync_state.get("last_hash"),
                                status="skipped",
                            )
                            message = f"{spec.title}: sem alteracao desde a ultima sincronizacao."
                            if message not in warnings:
                                warnings.append(message)
                            continue

                    catalog.add_source(source, chunks, persist=persist)
                    if persistence and persistence.enabled:
                        persistence.upsert_sync_state(
                            source_key=source_key,
                            source_id=source.source_id,
                            version_id=source.version_id,
                            last_hash=source.metadata.hash_documento,
                            status="synced",
                        )
                    source_ids.append(source.source_id)
                    imported_chunks += len(chunks)
                    for warning in bundle_warnings:
                        message = f"{spec.title}: {warning}"
                        if message not in warnings:
                            warnings.append(message)
                except Exception as exc:
                    failed_sources += 1
                    if persistence and persistence.enabled:
                        persistence.upsert_sync_state(
                            source_key=source_key,
                            source_id=None,
                            version_id=None,
                            last_hash=None,
                            status="failed",
                            last_error=str(exc),
                        )
                    message = f"{spec.title}: falha na ingestao ({exc})"
                    if message not in warnings:
                        warnings.append(message)
        finally:
            if persistence and persistence.enabled:
                persistence.finish_ingestion_job(
                    job_id,
                    status="completed" if failed_sources == 0 else "completed_with_errors",
                    imported_sources=len(source_ids),
                    imported_chunks=imported_chunks,
                    skipped_sources=skipped_sources,
                    failed_sources=failed_sources,
                    warnings=warnings,
                )

        return ManifestIngestionReport(
            job_id=job_id,
            imported_sources=len(source_ids),
            imported_chunks=imported_chunks,
            skipped_sources=skipped_sources,
            failed_sources=failed_sources,
            source_ids=source_ids,
            warnings=warnings,
        )

    def ingest_source_spec(self, spec: ManifestSourceSpec) -> tuple[SourceRecord, list[ChunkRecord], list[str], bool]:
        payload, detected_mime = self._load_payload_for_spec(spec)
        filename = self._derive_filename(spec)
        return self._build_source_bundle(
            title=spec.title,
            description=spec.description or spec.title,
            filename=filename,
            mime_type=spec.mime_type or detected_mime,
            payload=payload,
            source_type=spec.source_type,
            authority=spec.authority,
            is_official=spec.is_official,
            is_primary=spec.is_primary,
            hierarchy=spec.hierarchy,
            metadata=spec.metadata,
        )

    def _build_source_bundle(
        self,
        *,
        title: str,
        description: str,
        filename: str,
        mime_type: str,
        payload: bytes,
        source_type: SourceType,
        authority: SourceAuthority,
        is_official: bool,
        is_primary: bool,
        hierarchy: list[str],
        metadata: SourceMetadata,
    ) -> tuple[SourceRecord, list[ChunkRecord], list[str], bool]:
        text = load_bytes_as_text(filename, mime_type, payload)
        doc_hash = compute_document_hash(text)
        warnings: list[str] = []
        if not text:
            warnings.append("Nao foi possivel extrair texto do documento.")

        injection_detected = detect_prompt_injection(text)
        if injection_detected:
            warnings.append(
                "Possivel prompt injection detectado no documento. O conteudo sera tratado como dado nao confiavel."
            )

        metadata = metadata.model_copy(
            update={
                "hash_documento": doc_hash,
                "metadata_extra": {
                    **metadata.metadata_extra,
                    "original_filename": filename,
                    "mime_type": mime_type,
                },
            }
        )
        metadata = enrich_source_metadata(
            source_type=source_type,
            title=title,
            text=text,
            metadata=metadata,
        )
        source_id = stable_id(title, metadata.url_origem or filename, doc_hash)
        record = SourceRecord(
            source_id=source_id,
            document_id=stable_id("document", title, metadata.url_origem or filename),
            version_id=stable_id("version", title, doc_hash),
            title=title,
            source_type=source_type,
            authority=authority,
            is_official=is_official,
            is_primary=is_primary,
            description=description,
            raw_text=text,
            hierarchy=hierarchy,
            metadata=metadata,
        )
        chunks = chunk_source(record)
        return record, chunks, warnings, injection_detected

    @staticmethod
    def _derive_filename(spec: ManifestSourceSpec) -> str:
        if spec.path:
            return Path(spec.path).name
        if spec.url:
            return spec.url.rstrip("/").split("/")[-1] or stable_id(spec.title)
        return stable_id(spec.title)

    @staticmethod
    def _load_payload_for_spec(spec: ManifestSourceSpec) -> tuple[bytes, str]:
        if spec.path:
            return load_local_payload(spec.path)
        if spec.url:
            return fetch_remote_payload(spec.url)
        raise ValueError("Manifest source must define either 'path' or 'url'.")

    @staticmethod
    def _source_key(spec: ManifestSourceSpec) -> str:
        return spec.url or spec.path or spec.title
