from __future__ import annotations

import logging
import math

from backend.app.config.settings import settings
from backend.app.models.domain import RetrievedChunk

logger = logging.getLogger(__name__)


class RerankerService:
    def __init__(self) -> None:
        self.provider = settings.reranker_provider
        self.model_name = settings.reranker_model
        self.blend_weight = max(0.0, min(1.0, settings.reranker_blend_weight))
        self.candidate_limit = max(1, settings.reranker_candidate_limit)
        self._client = self._build_client()

    @property
    def active_backend(self) -> str:
        if self._client is not None:
            return f"{self.provider}:{self.model_name}"
        return "heuristic"

    def rerank(self, query: str, ranked: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if not ranked:
            return []

        window = ranked[: self.candidate_limit]
        if self._client is not None:
            scores = self._predict_scores(query, window)
        else:
            scores = [self._heuristic_score(query, item) for item in window]

        updated: list[RetrievedChunk] = []
        for item, score in zip(window, scores):
            normalized_score = max(0.0, min(1.0, float(score)))
            blended = ((1 - self.blend_weight) * item.final_score) + (self.blend_weight * normalized_score)
            reason = item.reason
            if "reranker" not in reason:
                reason = f"{reason}, reranker" if reason else "reranker"
            updated.append(
                item.model_copy(
                    update={
                        "rerank_score": round(normalized_score, 4),
                        "final_score": round(blended, 4),
                        "reason": reason,
                    }
                )
            )

        updated.sort(key=lambda chunk: chunk.final_score, reverse=True)
        remainder = ranked[self.candidate_limit :]
        return updated + remainder

    def _build_client(self):
        if self.provider != "cross_encoder":
            return None
        try:
            from sentence_transformers import CrossEncoder

            return CrossEncoder(self.model_name)
        except Exception as exc:  # pragma: no cover
            logger.warning(
                "Failed to initialize CrossEncoder reranker, falling back to heuristic rerank.",
                extra={"extra_payload": {"error": str(exc)}},
            )
            return None

    def _predict_scores(self, query: str, ranked: list[RetrievedChunk]) -> list[float]:
        pairs = [(query, item.chunk.search_text[:1200]) for item in ranked]
        raw_scores = self._client.predict(pairs)
        normalized: list[float] = []
        for score in raw_scores:
            value = float(score)
            if value < 0.0 or value > 1.0:
                value = 1 / (1 + math.exp(-value))
            normalized.append(value)
        return normalized

    @staticmethod
    def _heuristic_score(query: str, item: RetrievedChunk) -> float:
        lowered_query = query.lower()
        lowered_text = item.chunk.search_text.lower()
        score = item.rerank_score
        if lowered_query and lowered_query[:60] in lowered_text:
            score += 0.25
        if item.chunk.is_official:
            score += 0.15
        if item.chunk.metadata.numero_processo and item.chunk.metadata.numero_processo.lower() in lowered_query:
            score += 0.2
        return min(1.0, score)
