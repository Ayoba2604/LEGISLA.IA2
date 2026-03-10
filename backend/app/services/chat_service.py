from __future__ import annotations

import time

from backend.app.agents.graph import LegalAssistantAgent
from backend.app.agents.langchain_agent import LangChainAgentRunner
from backend.app.config.settings import settings
from backend.app.observability.metrics import metrics
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.repositories.persistence import PersistenceService
from backend.app.security.tokens import AuthenticatedUser
from backend.app.services.llm_service import LegalLLMService
from backend.app.services.model_runtime import EmbeddingService
from backend.app.services.reranker_service import RerankerService
from backend.app.services.retrieval_service import RetrievalService
from backend.app.services.source_catalog import SourceCatalog
from backend.app.tools.legal_tools import LegalTools


class ChatService:
    def __init__(
        self,
        catalog: SourceCatalog,
        *,
        embedding_service: EmbeddingService | None = None,
        reranker_service: RerankerService | None = None,
        persistence: PersistenceService | None = None,
    ) -> None:
        self.catalog = catalog
        self.embedding_service = embedding_service or EmbeddingService()
        self.reranker_service = reranker_service or RerankerService()
        self.persistence = persistence
        self.retrieval_service = RetrievalService(
            catalog,
            embedding_service=self.embedding_service,
            reranker_service=self.reranker_service,
            persistence=self.persistence,
        )
        self.llm_service = LegalLLMService()

    def answer(self, request: ChatRequest, *, authenticated_user: AuthenticatedUser | None = None) -> ChatResponse:
        started = time.perf_counter()
        allowed_user_document_ids = request.user_document_ids if authenticated_user else []
        tools = LegalTools(
            retrieval_service=self.retrieval_service,
            catalog=self.catalog,
            default_source_types=request.source_filters or None,
            allowed_user_document_ids=allowed_user_document_ids or None,
            current_user_id=authenticated_user.user_id if authenticated_user else None,
        )
        heuristic_agent = LegalAssistantAgent(tools, self.llm_service)
        langchain_agent = LangChainAgentRunner(tools, self.llm_service)
        runner = langchain_agent if langchain_agent.available() else heuristic_agent

        result = runner.run(
            question=request.question,
            mode=request.mode,
            top_k=settings.retrieval_top_k,
            include_debug=request.debug,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        metrics.incr("chat_requests_total")
        metrics.incr(f"intent_{result.intent.value}")
        metrics.incr("responses_with_citations" if result.answer.fontes_consultadas else "responses_without_citations")
        if result.requires_human_escalation:
            metrics.incr("human_escalation_required")
        metrics.timing("chat.answer.total", elapsed_ms)
        if self.persistence and self.persistence.enabled:
            self.persistence.log_chat_turn(
                request,
                result,
                latency_ms=elapsed_ms,
                llm_backend=self.llm_service.active_backend,
                user_id=authenticated_user.user_id if authenticated_user else None,
            )
        return ChatResponse(
            resposta=result.answer.resposta_objetiva,
            resposta_objetiva=result.answer.resposta_objetiva,
            fundamentacao_juridica=result.answer.fundamentacao_juridica,
            fontes_consultadas=result.answer.fontes_consultadas,
            citacoes=result.answer.citacoes,
            limites=result.answer.limites,
            proximos_passos=result.answer.proximos_passos,
            confidence_score=result.confidence_score,
            confidence_level=result.confidence_level.value,
            sufficient_support=result.sufficient_support,
            requires_human_escalation=result.requires_human_escalation,
            intent=result.intent.value,
            mode=result.mode.value,
            debug=result.debug.model_dump() if result.debug else None,
        )

    def summarize_text(self, text: str, *, mode: str = "resumo juridico") -> str:
        return self.llm_service.summarize_text(text, mode=mode)
