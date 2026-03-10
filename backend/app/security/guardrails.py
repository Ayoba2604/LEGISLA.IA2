from __future__ import annotations

from backend.app.core.enums import ConfidenceLevel, IntentType
from backend.app.models.domain import RetrievedChunk

PROMPT_INJECTION_MARKERS = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "desconsidere as instrucoes anteriores",
    "ignore todas as instrucoes anteriores",
    "ignore as instrucoes anteriores",
    "act as",
    "system prompt",
    "tool call",
    "responda sem citar fontes",
)


def detect_prompt_injection(text: str) -> bool:
    folded = (text or "").lower()
    return any(marker in folded for marker in PROMPT_INJECTION_MARKERS)


def assess_support_strength(retrieved: list[RetrievedChunk]) -> tuple[float, ConfidenceLevel]:
    if not retrieved:
        return 0.0, ConfidenceLevel.LOW

    top_score = retrieved[0].final_score
    average = sum(item.final_score for item in retrieved[:4]) / min(len(retrieved), 4)
    score = round((top_score * 0.6) + (average * 0.4), 4)

    if score >= 0.72:
        return score, ConfidenceLevel.HIGH
    if score >= 0.34:
        return score, ConfidenceLevel.MEDIUM
    return score, ConfidenceLevel.LOW


def requires_human_escalation(intent: IntentType, confidence: ConfidenceLevel, question: str) -> bool:
    lowered = question.lower()
    sensitive_markers = (
        "peticao",
        "acao judicial",
        "estrategia processual",
        "prazo fatal",
        "urgente",
        "risco criminal",
        "demissao",
        "prisao",
    )
    return intent == IntentType.ESCALATION or confidence == ConfidenceLevel.LOW or any(
        marker in lowered for marker in sensitive_markers
    )
