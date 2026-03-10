from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from backend.app.config.settings import settings
from backend.app.retrievers.hybrid import HybridRetriever
from backend.app.schemas.retrieval import RetrievalFilters
from backend.app.services.reranker_service import RerankerService
from backend.app.services.model_runtime import EmbeddingService
from backend.app.services.source_catalog import SourceCatalog

if TYPE_CHECKING:
    from backend.app.repositories.persistence import PersistenceService

logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(
        self,
        catalog: SourceCatalog,
        *,
        embedding_service: EmbeddingService | None = None,
        reranker_service: RerankerService | None = None,
        persistence: "PersistenceService | None" = None,
    ) -> None:
        self.catalog = catalog
        self.embedding_service = embedding_service or EmbeddingService()
        self.reranker_service = reranker_service or RerankerService()
        self.persistence = persistence
        self.retriever = HybridRetriever()

    def search(self, query: str, *, top_k: int, filters: RetrievalFilters | None = None):
        filters = filters or RetrievalFilters()
        if self._should_use_database():
            db_results = self.persistence.hybrid_search(query=query, filters=filters, top_k=top_k) if self.persistence else []
            if db_results:
                reranked = self.reranker_service.rerank(query, db_results[: self.reranker_service.candidate_limit])
                return self.retriever.select_diverse(query, reranked[: settings.retrieval_candidate_limit], top_k)
            if self._database_only():
                return []
        candidates = self._filtered_candidates(filters)
        ranked = [self.retriever.score_chunk(query, chunk) for chunk in candidates]
        ranked.sort(key=lambda item: item.final_score, reverse=True)
        reranked = self.reranker_service.rerank(query, ranked[: self.reranker_service.candidate_limit])
        return self.retriever.select_diverse(query, reranked[: settings.retrieval_candidate_limit], top_k)

    def _filtered_candidates(self, filters: RetrievalFilters) -> list:
        chunks = self.catalog.list_chunks()
        if filters.source_types:
            allowed = set(filters.source_types)
            chunks = [chunk for chunk in chunks if chunk.source_type.value in allowed]
        if filters.source_ids:
            allowed_source_ids = set(filters.source_ids)
            chunks = [chunk for chunk in chunks if chunk.source_id in allowed_source_ids]
        if filters.only_official:
            chunks = [chunk for chunk in chunks if chunk.is_official]
        if filters.only_user_documents:
            chunks = [chunk for chunk in chunks if chunk.source_type.value == "user_document"]
        if filters.owner_user_id:
            chunks = [
                chunk
                for chunk in chunks
                if chunk.metadata.metadata_extra.get("owner_user_id") == filters.owner_user_id
            ]
        if filters.tribunal:
            chunks = [chunk for chunk in chunks if chunk.metadata.tribunal == filters.tribunal]
        if filters.uf:
            chunks = [chunk for chunk in chunks if chunk.metadata.uf == filters.uf]
        if filters.ramo_direito:
            chunks = [chunk for chunk in chunks if chunk.metadata.ramo_direito == filters.ramo_direito]
        return chunks

    @staticmethod
    def _database_only() -> bool:
        from backend.app.config.settings import settings

        return settings.retrieval_backend == "db"

    def _should_use_database(self) -> bool:
        from backend.app.config.settings import settings

        return bool(self.persistence and self.persistence.enabled and settings.retrieval_backend in {"auto", "db"})
