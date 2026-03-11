from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from backend.app.config.settings import settings
from backend.app.core.enums import ResponseMode
from backend.app.models.domain import Citation, RetrievedChunk
from backend.app.prompts.system import (
    CITATION_VERIFIER_PROMPT,
    FINAL_RESPONSE_PROMPT,
    MAIN_AGENT_SYSTEM_PROMPT,
)
from backend.app.services.model_runtime import ChatModelFactory

logger = logging.getLogger(__name__)


@dataclass
class AnswerVerification:
    executed: bool = False
    verified: bool = True
    issues: list[str] = field(default_factory=list)
    raw_payload: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        if not self.executed:
            return "verificacao pos-geracao nao executada"
        if self.verified:
            return "resposta verificada sem inconsistencias"
        return f"resposta com {len(self.issues)} problema(s) de suporte"


@dataclass
class GeneratedAnswer:
    objective: str
    foundation: str
    limitations: list[str]
    next_steps: list[str]
    verification: AnswerVerification = field(default_factory=AnswerVerification)


class LegalLLMService:
    def __init__(self) -> None:
        self.provider = settings.llm_provider
        self.chat_model = ChatModelFactory().build_chat_model()

    @property
    def active_backend(self) -> str:
        if self.chat_model is None:
            return "deterministic"
        return f"{settings.llm_provider}:{settings.llm_model}"

    def generate_answer(
        self,
        *,
        question: str,
        mode: ResponseMode,
        retrieved: list[RetrievedChunk],
        citations: list[Citation],
        limitations: list[str],
    ) -> GeneratedAnswer:
        if self.provider == "mock" or not retrieved or self.chat_model is None:
            return self._build_deterministic_answer(question, mode, retrieved, citations, limitations)

        try:
            return self._generate_with_model(question, mode, retrieved, citations, limitations)
        except Exception as exc:  # pragma: no cover
            logger.exception(
                "LLM provider failed, using deterministic fallback",
                extra={"extra_payload": {"error": str(exc)}},
            )
            return self._build_deterministic_answer(question, mode, retrieved, citations, limitations)

    def verify_answer(
        self,
        *,
        question: str,
        objective: str,
        foundation: str,
        retrieved: list[RetrievedChunk],
        citations: list[Citation],
    ) -> AnswerVerification:
        if self.provider == "mock" or self.chat_model is None or not retrieved:
            return AnswerVerification()

        prompt = (
            f"{MAIN_AGENT_SYSTEM_PROMPT.strip()}\n\n"
            f"{CITATION_VERIFIER_PROMPT.strip()}\n\n"
            "Retorne apenas JSON valido com as chaves: verified, issues.\n"
            "verified deve ser boolean.\n"
            "issues deve ser uma lista de strings curtas e concretas.\n"
            "Nao inclua markdown, cercas de codigo ou texto fora do JSON."
        )
        answer_payload = {
            "resposta_objetiva": objective,
            "fundamentacao_juridica": foundation,
        }

        try:
            response = self.chat_model.invoke(
                [
                    ("system", prompt),
                    (
                        "human",
                        "Pergunta do usuario:\n"
                        f"{question}\n\n"
                        f"Resposta final: {json.dumps(answer_payload, ensure_ascii=False)}\n"
                        f"Citacoes disponiveis: {json.dumps(self._build_citation_payload(citations, limit=12), ensure_ascii=False)}\n"
                        f"Contexto recuperado: {json.dumps(self._build_context_payload(retrieved, limit=8, excerpt_chars=3200), ensure_ascii=False)}",
                    ),
                ]
            )
            payload = self._parse_json_payload(self._message_to_text(response))
            verified = self._coerce_bool(payload.get("verified"), default=True)
            issues = self._merge_unique(payload.get("issues"))
            if not verified and not issues:
                issues = [
                    "A resposta final contem afirmacoes juridicas ou citacoes sem suporte verificavel nas fontes recuperadas."
                ]
            logger.info(
                "Post-generation verification executed",
                extra={
                    "extra_payload": {
                        "backend": self.active_backend,
                        "verified": verified,
                        "issues": issues,
                    }
                },
            )
            return AnswerVerification(executed=True, verified=verified, issues=issues, raw_payload=payload)
        except Exception as exc:  # pragma: no cover
            logger.warning(
                "Post-generation verification failed.",
                extra={"extra_payload": {"backend": self.active_backend, "error": str(exc)}},
            )
            return AnswerVerification()

    def summarize_text(self, text: str, *, mode: str = "resumo juridico") -> str:
        excerpt = text[:1200].strip()
        if not excerpt:
            return "Nao foi possivel extrair conteudo suficiente para resumir."

        if self.chat_model is not None:
            try:
                response = self.chat_model.invoke(
                    [
                        (
                            "system",
                            "Voce resume documentos juridicos sem inventar fatos. "
                            "Se o texto for insuficiente, diga isso claramente em portugues do Brasil.",
                        ),
                        (
                            "human",
                            f"Modo: {mode}\n\nTexto:\n{excerpt}\n\n"
                            "Responda com um resumo curto, fiel e verificavel.",
                        ),
                    ]
                )
                content = self._message_to_text(response)
                if content:
                    return content
            except Exception as exc:  # pragma: no cover
                logger.warning(
                    "LLM summarize_text failed, using deterministic fallback.",
                    extra={"extra_payload": {"error": str(exc)}},
                )

        return f"{mode.capitalize()}: {excerpt[:400]}{'...' if len(excerpt) > 400 else ''}"

    def _generate_with_model(
        self,
        question: str,
        mode: ResponseMode,
        retrieved: list[RetrievedChunk],
        citations: list[Citation],
        limitations: list[str],
    ) -> GeneratedAnswer:
        context_payload = self._build_context_payload(retrieved, limit=5, excerpt_chars=900)
        citation_payload = self._build_citation_payload(citations, limit=8)
        prompt = (
            f"{MAIN_AGENT_SYSTEM_PROMPT.strip()}\n\n"
            f"{FINAL_RESPONSE_PROMPT.strip()}\n\n"
            "Retorne apenas JSON valido com as chaves: "
            "resposta_objetiva, fundamentacao_juridica, limites, proximos_passos.\n"
            "Cada item de limites e proximos_passos deve ser uma lista de strings.\n"
            "Nao inclua markdown, cercas de codigo ou texto fora do JSON."
        )
        response = self.chat_model.invoke(
            [
                ("system", prompt),
                (
                    "human",
                    "Pergunta do usuario:\n"
                    f"{question}\n\n"
                    f"Modo: {mode.value}\n"
                    f"Limitacoes ja conhecidas: {json.dumps(limitations, ensure_ascii=False)}\n"
                    f"Citacoes disponiveis: {json.dumps(citation_payload, ensure_ascii=False)}\n"
                    f"Contexto recuperado: {json.dumps(context_payload, ensure_ascii=False)}",
                ),
            ]
        )
        payload = self._parse_json_payload(self._message_to_text(response))
        objective = self._safe_string(payload.get("resposta_objetiva"))
        foundation = self._safe_string(payload.get("fundamentacao_juridica"))

        if not objective or not foundation:
            raise ValueError("Structured answer from chat model is incomplete.")

        verification = self.verify_answer(
            question=question,
            objective=objective,
            foundation=foundation,
            retrieved=retrieved,
            citations=citations,
        )
        final_limitations = self._merge_unique(limitations, payload.get("limites"), verification.issues)
        next_steps = self._merge_unique(payload.get("proximos_passos"))
        if not next_steps:
            next_steps = self._next_steps(mode, citations)

        return GeneratedAnswer(
            objective=objective,
            foundation=foundation,
            limitations=final_limitations,
            next_steps=next_steps,
            verification=verification,
        )

    def _build_deterministic_answer(
        self,
        question: str,
        mode: ResponseMode,
        retrieved: list[RetrievedChunk],
        citations: list[Citation],
        limitations: list[str],
    ) -> GeneratedAnswer:
        if not retrieved:
            objective = "Nao encontrei base suficiente na colecao disponivel para responder com seguranca."
            foundation = (
                "A pergunta exige suporte documental verificavel. No estado atual da base, nao ha fonte suficiente "
                "para sustentar uma resposta juridica confiavel."
            )
            next_steps = [
                "Informe a lei, artigo, tribunal ou contexto fatico especifico.",
                "Envie o documento relevante, se a duvida depender de contrato, decisao ou notificacao.",
            ]
            return GeneratedAnswer(
                objective=objective,
                foundation=foundation,
                limitations=limitations,
                next_steps=next_steps,
            )

        top = retrieved[:3]
        if mode == ResponseMode.FRIENDLY:
            objective = self._friendly_summary(question, top)
        else:
            objective = self._technical_summary(question, top)

        foundation_lines = [FINAL_RESPONSE_PROMPT.strip(), MAIN_AGENT_SYSTEM_PROMPT.strip()]
        foundation_lines.append("Base documental considerada:")
        foundation_lines.extend(f"- {item.chunk.title}: {item.chunk.content[:220]}" for item in top)
        foundation = "\n".join(foundation_lines)
        next_steps = self._next_steps(mode, citations)
        return GeneratedAnswer(
            objective=objective,
            foundation=foundation,
            limitations=limitations,
            next_steps=next_steps,
        )

    def _build_context_payload(
        self,
        retrieved: list[RetrievedChunk],
        *,
        limit: int,
        excerpt_chars: int,
    ) -> list[dict[str, Any]]:
        return [
            {
                "title": item.chunk.title,
                "source_type": item.chunk.source_type.value,
                "authority": item.chunk.authority.value,
                "is_official": item.chunk.is_official,
                "content": item.chunk.content[:excerpt_chars],
                "metadata": item.chunk.metadata.model_dump(mode="json"),
                "scores": {
                    "vector": round(item.vector_score, 4),
                    "lexical": round(item.lexical_score, 4),
                    "rerank": round(item.rerank_score, 4),
                    "final": round(item.final_score, 4),
                },
            }
            for item in retrieved[:limit]
        ]

    @staticmethod
    def _build_citation_payload(citations: list[Citation], *, limit: int) -> list[dict[str, Any]]:
        return [
            {
                "reference_label": citation.reference_label,
                "quote": citation.quote,
                "source_type": citation.source_type.value,
                "authority": citation.authority.value,
                "url": citation.url,
                "metadata": citation.metadata,
            }
            for citation in citations[:limit]
        ]

    @staticmethod
    def _friendly_summary(question: str, top: list[RetrievedChunk]) -> str:
        first = top[0].chunk
        return (
            f"Com base no material recuperado sobre '{question}', o ponto mais relevante e: "
            f"{first.content[:240]}{'...' if len(first.content) > 240 else ''}"
        )

    @staticmethod
    def _technical_summary(question: str, top: list[RetrievedChunk]) -> str:
        parts = [f"Consulta tecnica: {question}."]
        for item in top:
            parts.append(f"{item.chunk.title} [{item.chunk.source_type.value}] -> {item.chunk.content[:180]}")
        return " ".join(parts)

    @staticmethod
    def _next_steps(mode: ResponseMode, citations: list[Citation]) -> list[str]:
        base_steps = [
            "Confira a integra da fonte antes de adotar qualquer medida.",
            "Se houver caso concreto com risco relevante, consulte advogado ou defensoria.",
        ]
        if mode == ResponseMode.TECHNICAL and citations:
            base_steps.insert(
                0,
                "Valide a correspondencia entre a citacao recuperada e a versao vigente da norma ou julgado.",
            )
        return base_steps

    @staticmethod
    def _safe_string(value: Any) -> str:
        if isinstance(value, str):
            return value.strip()
        return ""

    @classmethod
    def _merge_unique(cls, *items: Any) -> list[str]:
        merged: list[str] = []
        for raw_item in items:
            if isinstance(raw_item, str):
                candidate_items = [raw_item]
            elif isinstance(raw_item, list):
                candidate_items = raw_item
            else:
                candidate_items = []
            for candidate in candidate_items:
                text = cls._safe_string(candidate)
                if text and text not in merged:
                    merged.append(text)
        return merged

    @staticmethod
    def _coerce_bool(value: Any, *, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes", "sim"}:
                return True
            if lowered in {"false", "0", "no", "nao"}:
                return False
        return default

    @staticmethod
    def _message_to_text(message: Any) -> str:
        content = getattr(message, "content", message)
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    texts.append(str(item.get("text", "")).strip())
                else:
                    texts.append(str(item).strip())
            return "\n".join(part for part in texts if part)
        return str(content).strip()

    @staticmethod
    def _parse_json_payload(content: str) -> dict[str, Any]:
        if not content:
            return {}
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if not match:
                raise
            return json.loads(match.group(0))
