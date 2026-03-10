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
from backend.app.core.enums import ResponseMode
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.repositories.persistence import PersistenceService
from backend.app.schemas.chat import ChatRequest
from backend.app.schemas.retrieval import RetrievalFilters
from backend.app.services.chat_service import ChatService
from backend.app.services.model_runtime import EmbeddingService
from backend.app.services.reranker_service import RerankerService
from backend.app.services.retrieval_service import RetrievalService
from backend.app.services.source_catalog import SourceCatalog

DATASET_PATH = ROOT / "backend" / "data" / "evaluation" / "official_e2e_dataset.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an end-to-end benchmark against PostgreSQL/pgvector with official Brazilian sources.")
    parser.add_argument("--registry", type=Path, default=settings.official_corpus_registry_path)
    parser.add_argument("--manifest", type=Path, default=settings.official_corpus_manifest_output_path)
    parser.add_argument("--snapshot-root", type=Path, default=settings.official_corpus_snapshot_dir)
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--purge-existing-corpus", action="store_true")
    parser.add_argument("--allow-memory-fallback", action="store_true")
    args = parser.parse_args()

    embedding_service = EmbeddingService()
    reranker_service = RerankerService()
    persistence = PersistenceService(embedding_service)
    database_status = persistence.database_status()
    if not args.allow_memory_fallback:
        if not persistence.enabled:
            raise SystemExit("DATABASE_URL nao configurada. O benchmark end-to-end com pgvector exige PostgreSQL.")
        if not database_status.get("connected"):
            raise SystemExit(f"Banco indisponivel: {database_status.get('error') or 'falha de conexao'}")
        if not database_status.get("pgvector_ready"):
            raise SystemExit("Extensao pgvector indisponivel no banco configurado.")

    if args.purge_existing_corpus and persistence.enabled:
        persistence.purge_corpus()

    build_report = None
    if not args.skip_build or not args.manifest.exists():
        builder = OfficialCorpusBuilder()
        build_report = builder.build_from_registry_file(
            registry_path=args.registry,
            manifest_output_path=args.manifest,
            snapshot_root=args.snapshot_root,
        )

    catalog = SourceCatalog(embedding_service=embedding_service, persistence=persistence)
    ingestion_pipeline = IngestionPipeline()
    ingestion_report = ingestion_pipeline.ingest_manifest(
        manifest_path=args.manifest,
        catalog=catalog,
        persist=persistence.enabled,
    )

    retrieval_service = RetrievalService(
        catalog,
        embedding_service=embedding_service,
        reranker_service=reranker_service,
        persistence=persistence,
    )
    chat_service = ChatService(
        catalog,
        embedding_service=embedding_service,
        reranker_service=reranker_service,
        persistence=persistence,
    )

    dataset = json.loads(args.dataset.read_text(encoding="utf-8"))
    original_backend = settings.retrieval_backend
    if persistence.enabled:
        settings.retrieval_backend = "db"

    rows = []
    retrieval_hits = 0
    citation_hits = 0
    response_citations = 0
    support_hits = 0

    try:
        for item in dataset:
            filters = RetrievalFilters(only_official=True, source_types=["legislation"])
            results = retrieval_service.search(item["question"], top_k=args.top_k, filters=filters)
            top = results[0] if results else None
            expected_title = item["expected_title_contains"].lower()
            expected_article = item["expected_article"].lower()
            retrieval_hit = bool(top) and expected_title in top.chunk.title.lower() and expected_article in top.chunk.content.lower()
            retrieval_hits += int(retrieval_hit)

            response = chat_service.answer(
                ChatRequest(question=item["question"], mode=ResponseMode.TECHNICAL, source_filters=["legislation"])
            )
            citation_hit = any(expected_title in citation.title.lower() for citation in response.fontes_consultadas)
            citation_hits += int(citation_hit)
            response_citations += int(bool(response.fontes_consultadas))
            support_hits += int(response.sufficient_support)

            rows.append(
                {
                    "id": item["id"],
                    "question": item["question"],
                    "top_title": top.chunk.title if top else None,
                    "top_source_type": top.chunk.source_type.value if top else None,
                    "top_score": round(top.final_score, 4) if top else None,
                    "retrieval_hit": retrieval_hit,
                    "citation_hit": citation_hit,
                    "response_has_citations": bool(response.fontes_consultadas),
                    "sufficient_support": response.sufficient_support,
                }
            )
    finally:
        settings.retrieval_backend = original_backend

    total = len(dataset)
    report = {
        "database": database_status,
        "build_report": build_report.model_dump(mode="json") if build_report else None,
        "ingestion_report": ingestion_report.model_dump(mode="json"),
        "total_questions": total,
        "retrieval_accuracy_at_1": round(retrieval_hits / total, 4) if total else 0.0,
        "citation_hit_rate": round(citation_hits / total, 4) if total else 0.0,
        "response_citation_rate": round(response_citations / total, 4) if total else 0.0,
        "sufficient_support_rate": round(support_hits / total, 4) if total else 0.0,
        "rows": rows,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

