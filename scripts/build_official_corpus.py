from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config.settings import settings
from backend.app.connectors.official_corpus import OfficialCorpusBuilder


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect official Brazilian legal sources and build a local corpus manifest.")
    parser.add_argument(
        "--registry",
        type=Path,
        default=settings.official_corpus_registry_path,
        help="Path to official corpus registry JSON.",
    )
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=settings.official_corpus_manifest_output_path,
        help="Output path for the generated corpus manifest.",
    )
    parser.add_argument(
        "--snapshot-root",
        type=Path,
        default=settings.official_corpus_snapshot_dir,
        help="Directory used to store downloaded official snapshots.",
    )
    args = parser.parse_args()

    builder = OfficialCorpusBuilder()
    report = builder.build_from_registry_file(
        registry_path=args.registry,
        manifest_output_path=args.manifest_output,
        snapshot_root=args.snapshot_root,
    )
    print(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

