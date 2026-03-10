from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.enums import SourceType
from backend.app.ingestion.pipeline import IngestionPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview ingestion for a single file.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--source-type", default="user_document")
    args = parser.parse_args()

    pipeline = IngestionPipeline()
    payload = args.path.read_bytes()
    source, chunks, warnings, injection = pipeline.ingest_upload(
        filename=args.path.name,
        mime_type="application/pdf" if args.path.suffix.lower() == ".pdf" else "text/plain",
        payload=payload,
        source_type=SourceType(args.source_type),
    )
    print(
        json.dumps(
            {
                "source_id": source.source_id,
                "chunk_count": len(chunks),
                "warnings": warnings,
                "prompt_injection": injection,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
