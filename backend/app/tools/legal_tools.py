from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.core.enums import IntentType
from backend.app.core.text import contains_article_reference, extract_article_number, extract_article_reference, fold_text, normalize_text
from backend.app.models.domain import Citation, ToolCallTrace
from backend.app.schemas.retrieval import RetrievalFilters
from backend.app.services.retrieval_service import RetrievalService
from backend.app.services.source_catalog import SourceCatalog

ARTICLE_CITATION_SOURCE_TYPES = {"legislation", "legacy_seed"}


def _normalize_article_reference(value: str | None) -> str | None:
    folded = fold_text(value or "").strip()
    return folded or None


def _quote_supported_by_chunk(quote: str, content: str) -> bool:
    normalized_quote = normalize_text(quote)
    normalized_content = normalize_text(content)
    if not normalized_quote:
        return False
    return normalized_quote in normalized_content


def build_citations_from_results(results) -> list[Citation]:
    citations: list[Citation] = []
    for item in results:
        chunk = item.chunk
        reference_parts = [chunk.title]
        if chunk.metadata.artigo:
            reference_parts.append(f"art. {chunk.metadata.artigo}")
        citations.append(
            Citation(
                citation_id=chunk.chunk_id,
                chunk_id=chunk.chunk_id,
                source_id=chunk.source_id,
                title=chunk.title,
                source_type=chunk.source_type,
                authority=chunk.authority,
                quote=chunk.content[:280],
                reference_label=" | ".join(reference_parts),
                url=chunk.metadata.url_origem,
                metadata={
                    "tribunal": chunk.metadata.tribunal,
                    "orgao_julgador": chunk.metadata.orgao_julgador,
                    "numero_processo": chunk.metadata.numero_processo,
                    "numero_norma": chunk.metadata.numero_norma,
                    "artigo": chunk.metadata.artigo,
                    "sumula_numero": chunk.metadata.sumula_numero,
                    "relator": chunk.metadata.relator,
                    "tema": chunk.metadata.tema,
                },
            )
        )
    return citations


@dataclass
class LegalTools:
    retrieval_service: RetrievalService
    catalog: SourceCatalog
    default_source_types: list[str] | None = None
    allowed_user_document_ids: list[str] | None = None
    current_user_id: str | None = None

    def _merged_filters(self, source_types: list[str] | None = None, overrides: dict[str, Any] | None = None) -> RetrievalFilters:
        merged_source_types = list(source_types or [])
        if self.default_source_types:
            if merged_source_types:
                allowed = set(self.default_source_types)
                merged_source_types = [item for item in merged_source_types if item in allowed]
            else:
                merged_source_types = list(self.default_source_types)
        payload = dict(overrides or {})
        payload["source_types"] = merged_source_types
        return RetrievalFilters(**payload)

    @staticmethod
    def serialize_results(results) -> list[dict[str, Any]]:
        return [
            {
                "chunk_id": item.chunk.chunk_id,
                "source_id": item.chunk.source_id,
                "title": item.chunk.title,
                "content": item.chunk.content[:500],
                "source_type": item.chunk.source_type.value,
                "authority": item.chunk.authority.value,
                "is_official": item.chunk.is_official,
                "final_score": item.final_score,
                "vector_score": item.vector_score,
                "lexical_score": item.lexical_score,
                "rerank_score": item.rerank_score,
                "reason": item.reason,
                "metadata": item.chunk.metadata.model_dump(mode="json"),
            }
            for item in results
        ]

    def buscar_legislacao(self, query: str, filtros: dict[str, Any] | None = None):
        filters = self._merged_filters(["legislation", "legacy_seed"], filtros)
        results = self.retrieval_service.search(query, top_k=4, filters=filters)
        trace = ToolCallTrace(tool_name="buscar_legislacao", input_payload={"query": query, "filtros": filtros or {}}, summary=f"{len(results)} chunks")
        return results, trace

    def buscar_jurisprudencia(self, query: str, filtros: dict[str, Any] | None = None):
        filters = self._merged_filters(["jurisprudence"], filtros)
        results = self.retrieval_service.search(query, top_k=4, filters=filters)
        trace = ToolCallTrace(tool_name="buscar_jurisprudencia", input_payload={"query": query, "filtros": filtros or {}}, summary=f"{len(results)} chunks")
        return results, trace

    def buscar_sumulas(self, query: str, filtros: dict[str, Any] | None = None):
        filters = self._merged_filters(["sumula"], filtros)
        results = self.retrieval_service.search(query, top_k=3, filters=filters)
        trace = ToolCallTrace(tool_name="buscar_sumulas", input_payload={"query": query, "filtros": filtros or {}}, summary=f"{len(results)} chunks")
        return results, trace

    def buscar_documentos_usuario(self, query: str, filtros: dict[str, Any] | None = None):
        if not self.current_user_id:
            trace = ToolCallTrace(
                tool_name="buscar_documentos_usuario",
                input_payload={"query": query, "filtros": filtros or {}},
                summary="acesso negado: autenticacao obrigatoria",
            )
            return [], trace
        overrides = dict(filtros or {})
        if self.allowed_user_document_ids:
            overrides["source_ids"] = self.allowed_user_document_ids
        if self.current_user_id:
            overrides["owner_user_id"] = self.current_user_id
        filters = self._merged_filters(["user_document"], overrides)
        results = self.retrieval_service.search(query, top_k=5, filters=filters)
        trace = ToolCallTrace(tool_name="buscar_documentos_usuario", input_payload={"query": query, "filtros": filtros or {}}, summary=f"{len(results)} chunks")
        return results, trace

    def buscar_contratos(self, query: str, filtros: dict[str, Any] | None = None):
        overrides = dict(filtros or {})
        source_types = ["contract"]
        if self.allowed_user_document_ids:
            overrides["source_ids"] = self.allowed_user_document_ids
        if self.current_user_id:
            source_types.append("user_document")
            overrides["owner_user_id"] = self.current_user_id
        results = self.retrieval_service.search(query, top_k=4, filters=self._merged_filters(source_types, overrides))
        trace = ToolCallTrace(
            tool_name="buscar_contratos",
            input_payload={"query": query, "filtros": filtros or {}},
            summary=f"{len(results)} chunks",
        )
        return results, trace

    def buscar_artigo_por_numero(self, lei: str, artigo: str):
        query = f"{lei} artigo {artigo}"
        filters = self._merged_filters(["legislation", "legacy_seed"])
        results = self.retrieval_service.search(query, top_k=3, filters=filters)
        requested_article = extract_article_number(artigo) or extract_article_number(query)
        if requested_article:
            results = [
                item
                for item in results
                if _normalize_article_reference(item.chunk.metadata.artigo) == requested_article
                or contains_article_reference(item.chunk.search_text, requested_article)
                or contains_article_reference(item.chunk.content, requested_article)
            ]
        trace = ToolCallTrace(tool_name="buscar_artigo_por_numero", input_payload={"lei": lei, "artigo": artigo}, summary=f"{len(results)} chunks")
        return results, trace

    def verificar_vigencia_norma(self, identificador: str):
        query = f"vigencia {identificador}"
        results = self.retrieval_service.search(query, top_k=3, filters=self._merged_filters(["legislation"]))
        summary = "vigencia nao encontrada na base"
        if results:
            summary = results[0].chunk.metadata.vigencia or "vigencia nao explicitada na base"
        return {"identificador": identificador, "resultado": summary}, ToolCallTrace(tool_name="verificar_vigencia_norma", input_payload={"identificador": identificador}, summary=summary)

    def listar_fontes_utilizadas(self, results):
        citations = build_citations_from_results(results)
        return citations, ToolCallTrace(tool_name="listar_fontes_utilizadas", summary=f"{len(citations)} fontes")

    def resumir_acordao(self, identifier: str):
        query = f"acordao {identifier}"
        results = self.retrieval_service.search(query, top_k=2, filters=self._merged_filters(["jurisprudence"]))
        summary = results[0].chunk.content if results else "Acordao nao encontrado na base."
        return summary, ToolCallTrace(tool_name="resumir_acordao", input_payload={"id": identifier}, summary="resumo preparado")

    def comparar_dispositivos(self, lista_de_normas: list[str]):
        query = " ".join(lista_de_normas)
        results = self.retrieval_service.search(
            query,
            top_k=min(6, max(2, len(lista_de_normas))),
            filters=self._merged_filters(["legislation", "legacy_seed"]),
        )
        comparison = [{"norma": item.chunk.title, "trecho": item.chunk.content[:220]} for item in results]
        return comparison, ToolCallTrace(tool_name="comparar_dispositivos", input_payload={"normas": lista_de_normas}, summary=f"{len(comparison)} trechos")

    def extrair_tese_juridica(self, acordao: str):
        results = self.retrieval_service.search(acordao, top_k=2, filters=self._merged_filters(["jurisprudence"]))
        thesis = results[0].chunk.content[:220] if results else "Tese nao encontrada."
        return thesis, ToolCallTrace(tool_name="extrair_tese_juridica", input_payload={"acordao": acordao}, summary="tese extraida")

    def analisar_contrato(self, texto_ou_documento: str):
        overrides = {}
        source_types = ["contract"]
        if self.current_user_id:
            source_types.append("user_document")
        if self.allowed_user_document_ids:
            overrides["source_ids"] = self.allowed_user_document_ids
        if self.current_user_id:
            overrides["owner_user_id"] = self.current_user_id
        results = self.retrieval_service.search(
            texto_ou_documento,
            top_k=4,
            filters=self._merged_filters(source_types, overrides),
        )
        analysis = [{"fonte": item.chunk.title, "ponto": item.chunk.content[:200]} for item in results]
        return analysis, ToolCallTrace(tool_name="analisar_contrato", summary=f"{len(analysis)} pontos")

    def cronologia_normativa(self, tema: str):
        results = self.retrieval_service.search(tema, top_k=5, filters=self._merged_filters(["legislation"]))
        timeline = [{"titulo": item.chunk.title, "data": str(item.chunk.metadata.data_publicacao) if item.chunk.metadata.data_publicacao else None} for item in results]
        return timeline, ToolCallTrace(tool_name="cronologia_normativa", input_payload={"tema": tema}, summary=f"{len(timeline)} eventos")

    def validar_citacoes(self, results, citations: list[Citation] | None = None):
        citations = citations or build_citations_from_results(results)
        chunks_by_id = {item.chunk.chunk_id: item.chunk for item in results}
        valid_count = 0
        invalid_count = 0
        issues: list[str] = []

        for citation in citations:
            chunk = chunks_by_id.get(citation.chunk_id)
            if chunk is None:
                invalid_count += 1
                issues.append(f"Citacao '{citation.reference_label}' aponta para chunk inexistente no contexto recuperado.")
                continue

            citation_issues: list[str] = []
            cited_article = _normalize_article_reference(extract_article_reference(citation.reference_label))
            chunk_article = _normalize_article_reference(chunk.metadata.artigo)

            if cited_article != chunk_article:
                citation_issues.append(
                    f"artigo em referencia divergente: esperado '{chunk.metadata.artigo or 'sem artigo'}', obtido '{cited_article or 'sem artigo'}'"
                )
            if not _quote_supported_by_chunk(citation.quote, chunk.content):
                citation_issues.append("quote nao localizada no conteudo do chunk")
            if citation.source_type != chunk.source_type:
                citation_issues.append("source_type divergente do chunk recuperado")
            if cited_article and citation.source_type.value not in ARTICLE_CITATION_SOURCE_TYPES:
                citation_issues.append("referencia por artigo em fonte cujo tipo nao sustenta citacao normativa")

            if citation_issues:
                invalid_count += 1
                issues.append(f"Citacao '{citation.reference_label}' invalida: {', '.join(citation_issues)}.")
            else:
                valid_count += 1

        summary = f"{len(citations)} citacoes verificadas, {invalid_count} invalidas"
        return {
            "validas": valid_count,
            "invalidas": invalid_count,
            "issues": issues,
        }, ToolCallTrace(tool_name="validar_citacoes", summary=summary)

    def classificar_tipo_pergunta(self, pergunta: str):
        lowered = fold_text(pergunta)
        article_ref = extract_article_reference(lowered)
        if article_ref:
            intent = IntentType.ARTICLE_LOOKUP
        elif any(marker in lowered for marker in ("acordao", "jurisprud", "stf", "stj", "tese", "sumula", "sumula")):
            intent = IntentType.JURISPRUDENCE_SUMMARY
        elif any(marker in lowered for marker in ("contrato", "clausula")):
            intent = IntentType.CONTRACT_ANALYSIS
        elif any(marker in lowered for marker in ("vigencia", "revogada", "revogado")):
            intent = IntentType.VALIDITY_CHECK
        elif any(marker in lowered for marker in ("compar", "conflito entre normas", "diferenca entre")):
            intent = IntentType.NORM_COMPARISON
        elif any(marker in lowered for marker in ("checklist", "documentos necessarios")):
            intent = IntentType.DOCUMENT_CHECKLIST
        elif any(marker in lowered for marker in ("peticao", "minuta", "parecer")):
            intent = IntentType.LEGAL_DRAFT
        elif any(marker in lowered for marker in ("meu documento", "arquivo anexado", "pdf anexado")):
            intent = IntentType.USER_DOCUMENT
        else:
            intent = IntentType.GENERAL_CONSULTATION
        return intent, ToolCallTrace(tool_name="classificar_tipo_pergunta", input_payload={"pergunta": pergunta}, summary=intent.value)

    def detectar_necessidade_de_escalonamento_humano(self, pergunta: str):
        lowered = fold_text(pergunta)
        needs_escalation = any(marker in lowered for marker in ("urgente", "prazo", "risco criminal", "audiencia"))
        return needs_escalation, ToolCallTrace(tool_name="detectar_necessidade_de_escalonamento_humano", input_payload={"pergunta": pergunta}, summary=str(needs_escalation))
