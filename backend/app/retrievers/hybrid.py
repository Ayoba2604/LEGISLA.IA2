from __future__ import annotations

from dataclasses import dataclass

from backend.app.config.settings import settings
from backend.app.core.text import (
    contains_article_reference,
    cosine_similarity,
    extract_article_number,
    fold_text,
    hashed_embedding,
    jaccard_similarity,
    lexical_overlap_score,
    tokenize,
)
from backend.app.models.domain import ChunkRecord, RetrievedChunk

LAW_REFERENCE_ALIASES = {
    "cc": ("codigo civil", "lei 10.406/2002", "10406"),
    "cdc": ("codigo de defesa do consumidor", "lei 8.078/1990", "8078"),
    "cf": (
        "constituicao da republica federativa do brasil",
        "constituicao federal",
        "cf/88",
    ),
    "cf88": (
        "constituicao da republica federativa do brasil",
        "constituicao federal",
        "cf/88",
    ),
    "clt": ("consolidacao das leis do trabalho", "decreto-lei 5.452/1943", "5452"),
    "cpc": ("codigo de processo civil", "lei 13.105/2015", "13105"),
    "lgpd": ("lei geral de protecao de dados pessoais", "lei 13.709/2018", "13709"),
}


@dataclass
class HybridRetriever:
    mmr_lambda: float = settings.retrieval_mmr_lambda

    def score_chunk(
        self,
        query: str,
        chunk: ChunkRecord,
        *,
        query_embedding: list[float] | None = None,
        chunk_embedding: list[float] | None = None,
    ) -> RetrievedChunk:
        query_embedding = query_embedding or hashed_embedding(query)
        if chunk_embedding is None:
            if chunk.embedding and len(chunk.embedding) == len(query_embedding):
                chunk_embedding = chunk.embedding
            else:
                chunk_embedding = hashed_embedding(chunk.search_text, dimensions=len(query_embedding))

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
        article_signal = self._article_query_signal(query, chunk)
        article_mismatch_penalty = self._article_mismatch_penalty(query, chunk)
        law_reference_signal = self._law_reference_signal(query, chunk)
        law_reference_mismatch_penalty = self._law_reference_mismatch_penalty(query, chunk)

        if extract_article_number(query):
            final_score = (
                0.10 * vector_score
                + 0.16 * lexical_score
                + 0.10 * official_priority
                + 0.02 * recency_score
                + 0.07 * source_type_priority
                + 0.12 * rerank_score
                + 0.28 * article_signal
                + 0.15 * law_reference_signal
                - article_mismatch_penalty
                - law_reference_mismatch_penalty
            )
        else:
            weights = settings.retrieval_weights
            final_score = (
                weights.vector * vector_score
                + weights.lexical * lexical_score
                + weights.official_priority * official_priority
                + weights.recency * recency_score
                + weights.source_type * source_type_priority
                + weights.rerank * rerank_score
                - law_reference_mismatch_penalty
            )

        return RetrievedChunk(
            chunk=chunk,
            vector_score=round(vector_score, 4),
            lexical_score=round(lexical_score, 4),
            rerank_score=round(rerank_score, 4),
            final_score=round(final_score, 4),
            reason=self._reason_text(chunk, lexical_score, vector_score, rerank_score, article_signal),
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
        lowered_query = fold_text(query)
        lowered_text = fold_text(chunk.search_text)
        article_number = extract_article_number(query)
        material_overlap = self._material_overlap(query, chunk, article_number)
        title_overlap = lexical_overlap_score(query, chunk.title)

        bonus = 0.0
        if lowered_query[:40] and lowered_query[:40] in lowered_text:
            bonus += 0.15
        if chunk.metadata.artigo and fold_text(chunk.metadata.artigo) in lowered_query:
            bonus += 0.2
        bonus += material_overlap * 0.45
        if title_overlap:
            bonus += min(0.25, title_overlap * 0.45)
        bonus += self._law_reference_signal(query, chunk) * 0.2
        return min(1.0, bonus)

    @staticmethod
    def _material_query_tokens(query: str, article_number: str | None) -> list[str]:
        ignored_tokens = {
            "a",
            "ao",
            "art",
            "artigo",
            "com",
            "da",
            "das",
            "de",
            "do",
            "dos",
            "e",
            "no",
            "o",
            "os",
            "qual",
            "quais",
            "que",
            "sobre",
        }
        tokens = []
        for token in tokenize(query):
            if token in ignored_tokens or token == article_number or token.isdigit():
                continue
            tokens.append(token)
        return tokens

    def _material_overlap(self, query: str, chunk: ChunkRecord, article_number: str | None) -> float:
        tokens = self._material_query_tokens(query, article_number)
        if not tokens:
            return 0.0
        return lexical_overlap_score(" ".join(tokens), f"{chunk.title} {chunk.search_text}")

    def _article_query_signal(self, query: str, chunk: ChunkRecord) -> float:
        article_number = extract_article_number(query)
        if not article_number:
            return 0.0

        signal = 0.0
        material_tokens = self._material_query_tokens(query, article_number)
        if contains_article_reference(chunk.search_text, article_number):
            signal += 0.75
        elif contains_article_reference(chunk.content, article_number):
            signal += 0.65

        material_overlap = self._material_overlap(query, chunk, article_number)
        if material_overlap:
            signal += material_overlap * 0.35
        elif signal and material_tokens:
            signal *= 0.3

        title_overlap = lexical_overlap_score(query, chunk.title)
        signal += title_overlap * 0.35
        return min(1.0, signal)

    @staticmethod
    def _article_mismatch_penalty(query: str, chunk: ChunkRecord) -> float:
        query_article = extract_article_number(query)
        if not query_article:
            return 0.0
        chunk_article = extract_article_number(chunk.search_text) or extract_article_number(chunk.content)
        if chunk_article and chunk_article != query_article:
            return 0.18
        return 0.0

    @staticmethod
    def _law_reference_signal(query: str, chunk: ChunkRecord) -> float:
        mentioned_laws = HybridRetriever._mentioned_law_keys(query)
        if not mentioned_laws:
            return 0.0

        for law_key in mentioned_laws:
            if HybridRetriever._chunk_matches_law_key(chunk, law_key):
                return 1.0
        return 0.0

    @staticmethod
    def _law_reference_mismatch_penalty(query: str, chunk: ChunkRecord) -> float:
        mentioned_laws = HybridRetriever._mentioned_law_keys(query)
        if not mentioned_laws:
            return 0.0
        if any(HybridRetriever._chunk_matches_law_key(chunk, law_key) for law_key in mentioned_laws):
            return 0.0
        return 0.22 if extract_article_number(query) else 0.12

    @staticmethod
    def _mentioned_law_keys(query: str) -> set[str]:
        lowered_query = fold_text(query)
        query_tokens = set(tokenize(query))
        if not lowered_query and not query_tokens:
            return set()

        matches: set[str] = set()
        for alias, targets in LAW_REFERENCE_ALIASES.items():
            if alias in query_tokens or any(target in lowered_query for target in targets):
                matches.add(alias)
        return matches

    @staticmethod
    def _chunk_matches_law_key(chunk: ChunkRecord, law_key: str) -> bool:
        targets = LAW_REFERENCE_ALIASES.get(law_key, ())
        haystack = " ".join(
            [
                fold_text(chunk.title),
                fold_text(chunk.metadata.numero_norma or ""),
                fold_text(chunk.search_text),
            ]
        )
        return any(target in haystack for target in targets)

    @staticmethod
    def _reason_text(
        chunk: ChunkRecord,
        lexical: float,
        vector: float,
        rerank: float,
        article_signal: float,
    ) -> str:
        reasons = []
        if lexical >= 0.2:
            reasons.append("match lexical")
        if vector >= 0.2:
            reasons.append("similaridade vetorial")
        if article_signal >= 0.55:
            reasons.append("artigo exato")
        if rerank > 0:
            reasons.append("boost juridico")
        if chunk.is_official:
            reasons.append("fonte oficial")
        return ", ".join(reasons) or "recuperacao hibrida"
