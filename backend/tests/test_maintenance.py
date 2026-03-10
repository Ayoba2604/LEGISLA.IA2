import json

from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.services.maintenance_service import MaintenanceService
from backend.app.services.source_catalog import SourceCatalog


class FakePersistence:
    enabled = True

    def __init__(self, source_id: str):
        self.source_id = source_id
        self.calls: list[tuple[int, bool]] = []

    def cleanup_expired_uploads(self, *, limit: int, hard_delete: bool):
        self.calls.append((limit, hard_delete))
        return {
            "processed_uploads": 1,
            "purged_sources": 1,
            "hard_deleted_uploads": int(hard_delete),
            "soft_deleted_uploads": int(not hard_delete),
            "source_ids": [self.source_id],
        }


def test_cleanup_expired_uploads_prunes_catalog():
    pipeline = IngestionPipeline()
    catalog = SourceCatalog()
    source, chunks, _, _ = pipeline.ingest_upload(
        filename="contrato.txt",
        mime_type="text/plain",
        payload=b"Clausula 1. O reajuste seguira indice oficial. Clausula 2. Multa limitada.",
    )
    catalog.add_source(source, chunks, persist=False)
    initial_chunks = len(catalog.chunks)

    persistence = FakePersistence(source.source_id)
    service = MaintenanceService(persistence=persistence)
    report = service.cleanup_expired_uploads(catalog=catalog, limit=20, hard_delete=False)

    assert persistence.calls == [(20, False)]
    assert report.processed_uploads == 1
    assert report.purged_sources == 1
    assert report.removed_chunks == initial_chunks
    assert source.source_id not in catalog.sources
    assert not catalog.chunks


def test_sync_manifest_imports_sources(tmp_path):
    source_path = tmp_path / "norma.txt"
    source_path.write_text("Art. 1. Esta norma de teste permanece vigente.", encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            [
                {
                    "title": "Norma operacional",
                    "source_type": "legislation",
                    "authority": "primary",
                    "path": str(source_path),
                    "is_official": True,
                    "is_primary": True,
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    catalog = SourceCatalog()
    service = MaintenanceService()
    report = service.sync_manifest(catalog=catalog, manifest_path=manifest_path, persist=False)

    assert report.imported_sources == 1
    assert report.failed_sources == 0
    assert len(catalog.sources) == 1

