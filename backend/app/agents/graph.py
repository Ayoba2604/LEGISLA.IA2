from __future__ import annotations

from backend.app.config.settings import settings
from backend.app.core.enums import IntentType
from backend.app.models.domain import AgentResult, AnswerSections, DebugTrace, RetrievedChunk, ToolCallTrace
from backend.app.observability.tracing import trace_step
from backend.app.security.guardrails import assess_support_strength, requires_human_escalation
from backend.app.services.llm_service import LegalLLMService
from backend.app.tools.legal_tools import LegalTools


class LegalAssistantAgent:
    def __init__(self, tools: LegalTools, llm_service: LegalLLMService) -> None:
        self.tools = tools
        self.llm_service = llm_service

    def run(self, *, question: str, mode, top_k: int, include_debug: bool) -> AgentResult:
        with trace_step("agent.classify_intent"):
            intent, intent_trace = self.tools.classificar_tipo_pergunta(question)

        tool_traces = [intent_trace]

        with trace_step("agent.retrieve"):
            retrieved, retrieval_traces = self._retrieve_for_intent(intent, question)
            tool_traces.extend(retrieval_traces)

        citations, citations_trace = self.tools.listar_fontes_utilizadas(retrieved)
        tool_traces.append(citations_trace)
        validation_result, validation_trace = self.tools.validar_citacoes(retrieved)
        tool_traces.append(validation_trace)
        support_score, confidence_level = assess_support_strength(retrieved)
        escalation, escalation_trace = self.tools.detectar_necessidade_de_escalonamento_humano(question)
        tool_traces.append(escalation_trace)

        limitations = []
        if not retrieved:
            limitations.append("Nao encontrei base suficiente na colecao carregada para responder com seguranca.")
        if any(item.chunk.source_type.value == "legacy_seed" for item in retrieved):
            limitations.append("Parte da resposta se apoia em seeds legadas de demonstracao, sem valor de fonte oficial.")
        if validation_result.get("invalidas"):
            limitations.append("Ha citacoes sem suporte robusto e elas nao devem ser tratadas como conclusivas.")
        if confidence_level.value == "low":
            limitations.append("Nivel de confianca baixo: a pergunta pede complementacao documental ou revisao humana.")

        with trace_step("agent.generate_answer"):
            objective, foundation, final_limitations, next_steps = self.llm_service.generate_answer(
                question=question,
                mode=mode,
                retrieved=retrieved[:top_k],
                citations=citations,
                limitations=limitations,
            )

        debug_trace = None
        if include_debug and settings.expose_debug_trace:
            debug_trace = DebugTrace(
                query=question,
                mode=mode,
                intent=intent,
                tools_called=tool_traces,
                retrieved_chunks=[
                    {
                        "chunk_id": item.chunk.chunk_id,
                        "title": item.chunk.title,
                        "source_type": item.chunk.source_type.value,
                        "score": item.final_score,
                        "reason": item.reason,
                    }
                    for item in retrieved
                ],
                reranked_chunks=[
                    {
                        "chunk_id": item.chunk.chunk_id,
                        "lexical": item.lexical_score,
                        "vector": item.vector_score,
                        "rerank": item.rerank_score,
                        "final_score": item.final_score,
                    }
                    for item in retrieved
                ],
                final_context=[
                    {
                        "title": item.chunk.title,
                        "content": item.chunk.content[:280],
                    }
                    for item in retrieved[:top_k]
                ],
                response_preview=objective,
                confidence_score=support_score,
            )

        answer = AnswerSections(
            resposta_objetiva=objective,
            fundamentacao_juridica=foundation,
            fontes_consultadas=citations,
            citacoes=[citation.reference_label for citation in citations],
            limites=final_limitations,
            proximos_passos=next_steps,
        )
        return AgentResult(
            answer=answer,
            confidence_score=support_score,
            confidence_level=confidence_level,
            intent=intent,
            mode=mode,
            sufficient_support=bool(retrieved) and confidence_level.value != "low",
            requires_human_escalation=escalation or requires_human_escalation(intent, confidence_level, question),
            debug=debug_trace,
            retrieved_chunks=retrieved,
            tool_traces=tool_traces,
        )

    def _retrieve_for_intent(self, intent: IntentType, question: str) -> tuple[list[RetrievedChunk], list[ToolCallTrace]]:
        traces: list[ToolCallTrace] = []
        if intent == IntentType.ARTICLE_LOOKUP:
            retrieved, trace = self.tools.buscar_artigo_por_numero("norma nao especificada", question)
            traces.append(trace)
            return retrieved, traces

        if intent == IntentType.JURISPRUDENCE_SUMMARY:
            retrieved, trace = self.tools.buscar_jurisprudencia(question)
            traces.append(trace)
            return retrieved, traces

        if intent == IntentType.CONTRACT_ANALYSIS:
            contracts, contract_trace = self.tools.buscar_contratos(question)
            legislation, legislation_trace = self.tools.buscar_legislacao(question)
            traces.extend([contract_trace, legislation_trace])
            return self._merge_results(contracts, legislation), traces

        if intent == IntentType.USER_DOCUMENT:
            documents, document_trace = self.tools.buscar_documentos_usuario(question)
            legislation, legislation_trace = self.tools.buscar_legislacao(question)
            traces.extend([document_trace, legislation_trace])
            return self._merge_results(documents, legislation, prioritized_source_type="user_document"), traces

        retrieved, trace = self.tools.buscar_legislacao(question)
        traces.append(trace)
        return retrieved, traces

    @staticmethod
    def _merge_results(
        *groups: list[RetrievedChunk],
        prioritized_source_type: str | None = None,
    ) -> list[RetrievedChunk]:
        merged: list[RetrievedChunk] = []
        seen = set()
        for group in groups:
            for item in group:
                if item.chunk.chunk_id in seen:
                    continue
                seen.add(item.chunk.chunk_id)
                merged.append(item)
        if prioritized_source_type:
            merged.sort(
                key=lambda item: (
                    item.chunk.source_type.value != prioritized_source_type,
                    -item.final_score,
                )
            )
        else:
            merged.sort(key=lambda item: item.final_score, reverse=True)
        return merged
