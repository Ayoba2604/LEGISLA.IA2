from __future__ import annotations

from dataclasses import dataclass

from backend.app.config.settings import settings
from backend.app.core.text import (
    contains_article_reference,
    cosine_similarity,
    extract_article_number,
    hashed_embedding,
    jaccard_similarity,
    lexical_overlap_score,
    tokenize,
)
from backend.app.models.domain import ChunkRecord, RetrievedChunk


@dataclass
class HybridRetriever:
    mmr_lambda: float = settings.retrieval_mmr_lambda

    def score_chunk(self, query: str, chunk: ChunkRecord) -> RetrievedChunk:
        query_embedding = hashed_embedding(query)
        chunk_embedding = chunk.embedding or hashed_embedding(chunk.search_text)

        vector_score = cosine_similarity(query_embedding, chunk_embedding)
        lexical_score = lexical_overlap_score(query, chunk.search_text)
        return self.build_scored_result(query=query, chunk=chunk, vector_score=vector_score, lexical_score=lexical_score)

    def build_scored_result(
        self,
        *,
        query: str,
        chunk: ChunkRecord,
        vector_score: float,
        lexical_score: float,
    ) -> RetrievedChunk:
        vector_score = max(0.0, min(1.0, vector_score))
        lexical_score = max(0.0, min(1.0, lexical_score))
        official_priority = 1.0 if chunk.is_official else 0.35
        source_type_priority = settings.source_type_priority(chunk.source_type.value)
        recency_score = 0.5 if chunk.metadata.data_publicacao else 0.2
        rerank_score = self._rerank(query, chunk)

        weights = settings.retrieval_weights
        final_score = (
            weights.vector * vector_score
            + weights.lexical * lexical_score
            + weights.official_priority * official_priority
            + weights.recency * recency_score
            + weights.source_type * source_type_priority
            + weights.rerank * rerank_score
        )

        return RetrievedChunk(
            chunk=chunk,
            vector_score=round(vector_score, 4),
            lexical_score=round(lexical_score, 4),
            rerank_score=round(rerank_score, 4),
            final_score=round(final_score, 4),
            reason=self._reason_text(chunk, lexical_score, vector_score, rerank_score),
        )

    def select_diverse(self, query: str, ranked: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
        selected: list[RetrievedChunk] = []
        query_tokens = tokenize(query)
        pool = ranked[:]

        while pool and len(selected) < top_k:
            best_index = 0
            best_score = float("-inf")
            for index, candidate in enumerate(pool):
                relevance = candidate.final_score
                if not selected:
                    diversity_penalty = 0.0
                else:
                    max_similarity = max(
                        jaccard_similarity(query_tokens + tokenize(candidate.chunk.content), tokenize(item.chunk.content))
                        for item in selected
                    )
                    diversity_penalty = (1 - self.mmr_lambda) * max_similarity
                mmr_score = (self.mmr_lambda * relevance) - diversity_penalty
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_index = index
            selected.append(pool.pop(best_index))
        return selected

    def _rerank(self, query: str, chunk: ChunkRecord) -> float:
        lowered_query = query.lower()
        lowered_text = chunk.search_text.lower()
        bonus = 0.0
        article_number = extract_article_number(query)

        if any(marker in lowered_query for marker in ("art.", "artigo", "lei", "codigo", "sumula", "súmula", "sumula")):
            bonus += 0.2
        if lowered_query[:40] and lowered_query[:40] in lowered_text:
            bonus += 0.2
        if chunk.metadata.artigo and chunk.metadata.artigo.lower() in lowered_query:
            bonus += 0.3
        if contains_article_reference(chunk.search_text, article_number):
            bonus += 0.55
        elif contains_article_reference(chunk.content, article_number):
            bonus += 0.45
        if lexical_overlap_score(query, chunk.title) >= 0.4:
            bonus += 0.15
        return min(1.0, bonus)

    @staticmethod
    def _reason_text(chunk: ChunkRecord, lexical: float, vector: float, rerank: float) -> str:
        reasons = []
        if lexical >= 0.2:
            reasons.append("match lexical")
        if vector >= 0.2:
            reasons.append("similaridade vetorial")
        if rerank > 0:
            reasons.append("boost juridico")
        if chunk.is_official:
            reasons.append("fonte oficial")
        return ", ".join(reasons) or "recuperacao hibrida"

