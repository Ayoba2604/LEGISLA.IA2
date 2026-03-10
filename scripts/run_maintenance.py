from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config.settings import settings
from backend.app.repositories.persistence import PersistenceService
from backend.app.services.maintenance_service import MaintenanceService
from backend.app.services.model_runtime import EmbeddingService
from backend.app.services.source_catalog import SourceCatalog


def main() -> None:
    parser = argparse.ArgumentParser(description="Run corpus sync and retention maintenance tasks.")
    parser.add_argument("--sync-manifest", action="store_true", help="Run a manifest synchronization.")
    parser.add_argument("--cleanup-expired-uploads", action="store_true", help="Cleanup expired user uploads.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=settings.bootstrap_manifest_path,
        help="Path to corpus manifest used during sync.",
    )
    parser.add_argument("--no-persist", action="store_true", help="Sync only into memory without PostgreSQL writes.")
    parser.add_argument("--limit", type=int, default=settings.maintenance_cleanup_batch_size, help="Cleanup batch size.")
    parser.add_argument("--hard-delete", action="store_true", help="Delete upload audit rows after purging sources.")
    args = parser.parse_args()

    if not args.sync_manifest and not args.cleanup_expired_uploads:
        parser.error("Select at least one action: --sync-manifest and/or --cleanup-expired-uploads.")

    embedding_service = EmbeddingService()
    persistence = PersistenceService(embedding_service)
    catalog = SourceCatalog(embedding_service=embedding_service, persistence=persistence)
    catalog.load_bootstrap_sources()
    maintenance = MaintenanceService(persistence=persistence)

    output: dict[str, object] = {}

    if args.sync_manifest:
        report = maintenance.sync_manifest(
            catalog=catalog,
            manifest_path=args.manifest,
            persist=not args.no_persist,
        )
        output["sync_manifest"] = report.model_dump(mode="json")

    if args.cleanup_expired_uploads:
        report = maintenance.cleanup_expired_uploads(
            catalog=catalog,
            limit=args.limit,
            hard_delete=args.hard_delete,
        )
        output["cleanup_expired_uploads"] = report.model_dump(mode="json")

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

