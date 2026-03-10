from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config.settings import settings
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.repositories.persistence import PersistenceService
from backend.app.services.model_runtime import EmbeddingService
from backend.app.services.source_catalog import SourceCatalog


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a legal corpus manifest into the runtime catalog and database.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=settings.bootstrap_manifest_path,
        help="Path to corpus_manifest.json",
    )
    parser.add_argument(
        "--no-persist",
        action="store_true",
        help="Import only into memory without writing to PostgreSQL.",
    )
    args = parser.parse_args()

    embedding_service = EmbeddingService()
    persistence = PersistenceService(embedding_service)
    catalog = SourceCatalog(embedding_service=embedding_service, persistence=persistence)
    pipeline = IngestionPipeline()
    report = pipeline.ingest_manifest(
        manifest_path=args.manifest,
        catalog=catalog,
        persist=not args.no_persist,
    )
    print(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
