from __future__ import annotations

import json
import logging
from typing import Any

from backend.app.config.settings import settings
from backend.app.models.domain import AgentResult, AnswerSections, DebugTrace, ToolCallTrace
from backend.app.prompts.system import MAIN_AGENT_SYSTEM_PROMPT
from backend.app.security.guardrails import assess_support_strength, requires_human_escalation
from backend.app.services.llm_service import LegalLLMService
from backend.app.services.model_runtime import ChatModelFactory
from backend.app.tools.legal_tools import LegalTools, build_citations_from_results

logger = logging.getLogger(__name__)


class LangChainAgentRunner:
    def __init__(self, tools: LegalTools, llm_service: LegalLLMService) -> None:
        self.tools = tools
        self.llm_service = llm_service
        self.model = ChatModelFactory().build_chat_model()

    def available(self) -> bool:
        if not settings.use_langgraph_agent or self.model is None:
            return False
        try:
            from langchain.agents import create_agent  # noqa: F401
            from langchain_core.tools import tool  # noqa: F401

            return True
        except Exception:
            return False

    def run(self, *, question: str, mode, top_k: int, include_debug: bool) -> AgentResult:
        from langchain.agents import create_agent
        from langchain_core.tools import tool

        intent, intent_trace = self.tools.classificar_tipo_pergunta(question)

        @tool
        def buscar_legislacao(query: str) -> str:
            """Busca legislacao e normas relacionadas a consulta."""
            results, trace = self.tools.buscar_legislacao(query)
            return self._tool_payload("buscar_legislacao", trace, results)

        @tool
        def buscar_jurisprudencia(query: str) -> str:
            """Busca jurisprudencia e acordaos relacionados a consulta."""
            results, trace = self.tools.buscar_jurisprudencia(query)
            return self._tool_payload("buscar_jurisprudencia", trace, results)

        @tool
        def buscar_sumulas(query: str) -> str:
            """Busca sumulas relevantes para a pergunta."""
            results, trace = self.tools.buscar_sumulas(query)
            return self._tool_payload("buscar_sumulas", trace, results)

        @tool
        def buscar_contratos(query: str) -> str:
            """Busca contratos e clausulas relevantes para a pergunta."""
            results, trace = self.tools.buscar_contratos(query)
            return self._tool_payload("buscar_contratos", trace, results)

        @tool
        def buscar_documentos_usuario(query: str) -> str:
            """Busca documentos enviados pelo usuario relacionados a pergunta."""
            results, trace = self.tools.buscar_documentos_usuario(query)
            return self._tool_payload("buscar_documentos_usuario", trace, results)

        @tool
        def buscar_artigo_por_numero(lei: str, artigo: str) -> str:
            """Busca um artigo especifico em uma lei ou norma."""
            results, trace = self.tools.buscar_artigo_por_numero(lei, artigo)
            return self._tool_payload("buscar_artigo_por_numero", trace, results)

        @tool
        def verificar_vigencia_norma(identificador: str) -> str:
            """Verifica vigencia ou revogacao de uma norma."""
            payload, trace = self.tools.verificar_vigencia_norma(identificador)
            return json.dumps(
                {"tool_name": "verificar_vigencia_norma", "trace": trace.model_dump(), "payload": payload},
                ensure_ascii=False,
            )

        @tool
        def analisar_contrato(texto_ou_documento: str) -> str:
            """Analisa contrato ou documento contratual em busca de pontos relevantes."""
            payload, trace = self.tools.analisar_contrato(texto_ou_documento)
            return json.dumps(
                {"tool_name": "analisar_contrato", "trace": trace.model_dump(), "payload": payload},
                ensure_ascii=False,
            )

        @tool
        def comparar_dispositivos(normas: list[str]) -> str:
            """Compara dispositivos, leis ou normas informadas."""
            payload, trace = self.tools.comparar_dispositivos(normas)
            return json.dumps(
                {"tool_name": "comparar_dispositivos", "trace": trace.model_dump(), "payload": payload},
                ensure_ascii=False,
            )

        @tool
        def extrair_tese_juridica(acordao: str) -> str:
            """Extrai a tese juridica de um acordao recuperado."""
            payload, trace = self.tools.extrair_tese_juridica(acordao)
            return json.dumps(
                {"tool_name": "extrair_tese_juridica", "trace": trace.model_dump(), "payload": payload},
                ensure_ascii=False,
            )

        tools = [
            buscar_legislacao,
            buscar_jurisprudencia,
            buscar_sumulas,
            buscar_contratos,
            buscar_documentos_usuario,
            buscar_artigo_por_numero,
            verificar_vigencia_norma,
            analisar_contrato,
            comparar_dispositivos,
            extrair_tese_juridica,
        ]

        system_prompt = (
            f"{MAIN_AGENT_SYSTEM_PROMPT.strip()}\n"
            f"Intencao detectada: {intent.value}.\n"
            f"Modo de resposta: {mode.value}.\n"
            "Use tools quando precisar base documental. Nao invente citacoes."
        )

        agent = create_agent(model=self.model, tools=tools, system_prompt=system_prompt)
        result = agent.invoke({"messages": [{"role": "user", "content": question}]})
        messages = result.get("messages", [])

        tool_payloads = self._extract_tool_payloads(messages)
        recovered_results = self._recovered_results(tool_payloads)
        citations = self._extract_citations(tool_payloads)
        raw_answer = self._last_ai_content(messages)

        traces = [intent_trace]
        traces.extend(
            ToolCallTrace(
                tool_name=payload.get("tool_name", "unknown"),
                input_payload=payload.get("trace", {}).get("input_payload", {}),
                summary=payload.get("trace", {}).get("summary", ""),
            )
            for payload in tool_payloads
        )

        support_score, confidence_level = assess_support_strength(recovered_results)
        limitations = []
        if not citations:
            limitations.append("O agente nao encontrou citacoes suficientes no fluxo de tool calling.")
        if any(citation.source_type.value == "legacy_seed" for citation in citations):
            limitations.append("Parte da base ainda vem de seeds legados; isso nao substitui fonte oficial.")
        if confidence_level.value == "low":
            limitations.append("A resposta precisa de complementacao documental ou revisao humana.")

        if not raw_answer:
            raw_answer, foundation, limitations, next_steps = self.llm_service.generate_answer(
                question=question,
                mode=mode,
                retrieved=recovered_results[:top_k],
                citations=citations,
                limitations=limitations,
            )
        else:
            foundation = self._build_foundation(tool_payloads)
            next_steps = [
                "Valide os identificadores e a versao vigente da norma antes de usar a resposta.",
                "Se houver impacto relevante no caso concreto, escale para revisao humana.",
            ]

        debug_trace = None
        if include_debug and settings.expose_debug_trace:
            debug_trace = DebugTrace(
                query=question,
                mode=mode,
                intent=intent,
                tools_called=traces,
                retrieved_chunks=[
                    {"tool": payload.get("tool_name"), "results": payload.get("results", [])}
                    for payload in tool_payloads
                ],
                reranked_chunks=[
                    {
                        "chunk_id": item.chunk.chunk_id,
                        "score": item.final_score,
                        "reason": item.reason,
                    }
                    for item in recovered_results
                ],
                final_context=[
                    {
                        "title": citation.title,
                        "reference": citation.reference_label,
                        "quote": citation.quote,
                    }
                    for citation in citations
                ],
                response_preview=raw_answer,
                confidence_score=support_score,
            )

        answer = AnswerSections(
            resposta_objetiva=raw_answer,
            fundamentacao_juridica=foundation,
            fontes_consultadas=citations,
            citacoes=[citation.reference_label for citation in citations],
            limites=limitations,
            proximos_passos=next_steps,
        )
        return AgentResult(
            answer=answer,
            confidence_score=support_score,
            confidence_level=confidence_level,
            intent=intent,
            mode=mode,
            sufficient_support=bool(citations) and confidence_level.value != "low",
            requires_human_escalation=requires_human_escalation(intent, confidence_level, question),
            debug=debug_trace,
            retrieved_chunks=recovered_results,
            tool_traces=traces,
        )

    def _tool_payload(self, tool_name: str, trace: ToolCallTrace, results) -> str:
        payload = {
            "tool_name": tool_name,
            "trace": trace.model_dump(),
            "results": self.tools.serialize_results(results),
            "citations": [citation.model_dump(mode="json") for citation in build_citations_from_results(results)],
        }
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def _extract_tool_payloads(messages: list[Any]) -> list[dict[str, Any]]:
        payloads: list[dict[str, Any]] = []
        for message in messages:
            content = getattr(message, "content", None)
            if not content:
                continue
            if isinstance(message, dict):
                role = message.get("role")
                content = message.get("content")
            else:
                role = getattr(message, "type", None) or message.__class__.__name__.lower()
            if role not in {"tool", "toolmessage"}:
                continue
            try:
                payloads.append(json.loads(content))
            except Exception:
                continue
        return payloads

    @staticmethod
    def _last_ai_content(messages: list[Any]) -> str:
        for message in reversed(messages):
            content = getattr(message, "content", None)
            if isinstance(message, dict):
                if message.get("role") == "assistant" and not message.get("tool_calls"):
                    return message.get("content", "")
            elif message.__class__.__name__ == "AIMessage" and not getattr(message, "tool_calls", None):
                return content or ""
        return ""

    def _recovered_results(self, payloads: list[dict[str, Any]]):
        recovered = []
        for payload in payloads:
            for item in payload.get("results", []):
                chunk = self.tools.catalog.chunks.get(item.get("chunk_id"))
                if chunk is None:
                    continue
                recovered.append(
                    self.tools.retrieval_service.retriever.build_scored_result(
                        query="",
                        chunk=chunk,
                        vector_score=item.get("vector_score", 0.0),
                        lexical_score=item.get("lexical_score", 0.0),
                    )
                )
        return recovered

    @staticmethod
    def _extract_citations(payloads: list[dict[str, Any]]):
        citations = []
        for payload in payloads:
            for citation in payload.get("citations", []):
                citations.append(citation)
        from backend.app.models.domain import Citation

        return [Citation.model_validate(item) for item in citations]

    @staticmethod
    def _build_foundation(payloads: list[dict[str, Any]]) -> str:
        lines = ["Fluxo LangChain/LangGraph com tool calling executado."]
        for payload in payloads:
            trace = payload.get("trace", {})
            lines.append(f"- {payload.get('tool_name')}: {trace.get('summary', '')}")
            for item in payload.get("results", [])[:2]:
                lines.append(f"  - {item.get('title')}: {item.get('content')}")
        return "\n".join(lines)
