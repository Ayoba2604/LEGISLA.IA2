import json

from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.services.source_catalog import SourceCatalog


def test_ingestion_generates_chunks():
    pipeline = IngestionPipeline()
    source, chunks, warnings, injection = pipeline.ingest_upload(
        filename="contrato.txt",
        mime_type="text/plain",
        payload=b"CLAUSULA 1. O LOCATARIO pagara o aluguel mensal. CLAUSULA 2. O reajuste seguira o indice previsto.",
    )

    assert source.source_id
    assert chunks
    assert isinstance(warnings, list)
    assert injection is False


def test_manifest_ingestion_imports_local_sources(tmp_path):
    source_path = tmp_path / "lei.txt"
    source_path.write_text("Art. 1. Esta norma de teste esta vigente.", encoding="utf-8")
    manifest_path = tmp_path / "corpus_manifest.json"
    manifest_path.write_text(
        json.dumps(
            [
                {
                    "title": "Norma de teste",
                    "source_type": "legislation",
                    "authority": "primary",
                    "path": str(source_path),
                    "is_official": True,
                    "is_primary": True,
                    "metadata": {
                        "numero_norma": "Lei 9999/2026",
                        "vigencia": "vigente",
                    },
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    pipeline = IngestionPipeline()
    catalog = SourceCatalog()
    report = pipeline.ingest_manifest(manifest_path=manifest_path, catalog=catalog, persist=False)

    assert report.imported_sources == 1
    assert report.imported_chunks >= 1
    assert report.source_ids
    assert any(source.source_type.value == "legislation" for source in catalog.sources.values())
