from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.schemas.retrieval import RetrievalFilters
from backend.app.services.retrieval_service import RetrievalService
from backend.app.services.source_catalog import SourceCatalog

DATASET_PATH = ROOT / "backend" / "data" / "bootstrap" / "evaluation_dataset.json"


def main() -> None:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    catalog = SourceCatalog()
    catalog.load_bootstrap_sources()
    service = RetrievalService(catalog)

    total = len(dataset)
    retrieval_hits = 0
    citation_ready = 0
    rows = []

    for item in dataset:
        results = service.search(item["question"], top_k=3, filters=RetrievalFilters())
        hit = bool(results) and results[0].chunk.source_type.value == item["expected_source_type"]
        retrieval_hits += int(hit)
        citation_ready += int(bool(results) and bool(results[0].chunk.content))
        rows.append(
            {
                "id": item["id"],
                "question": item["question"],
                "top_source_type": results[0].chunk.source_type.value if results else None,
                "top_title": results[0].chunk.title if results else None,
                "hit": hit,
            }
        )

    report = {
        "total_questions": total,
        "retrieval_accuracy_at_1": round(retrieval_hits / total, 4) if total else 0.0,
        "citation_ready_rate": round(citation_ready / total, 4) if total else 0.0,
        "rows": rows,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
