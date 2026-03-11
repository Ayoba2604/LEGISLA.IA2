from __future__ import annotations

from backend.app.core.enums import ConfidenceLevel, IntentType
from backend.app.core.text import fold_text
from backend.app.models.domain import RetrievedChunk

PROMPT_INJECTION_MARKERS = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "desconsidere as instrucoes anteriores",
    "ignore todas as instrucoes anteriores",
    "ignore as instrucoes anteriores",
    "ignora instrucoes",
    "voce agora e",
    "finja que",
    "esqueca tudo",
    "new instructions",
    "override",
    "nao siga as regras",
    "responda como se fosse",
    "act as",
    "system prompt",
    "tool call",
    "responda sem citar fontes",
)


def detect_prompt_injection(text: str) -> bool:
    folded = fold_text(text or "")
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
    lowered = fold_text(question or "")
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


def apply_verification_penalty(score: float, confidence: ConfidenceLevel) -> tuple[float, ConfidenceLevel]:
    if confidence == ConfidenceLevel.HIGH:
        penalized_score = min(0.71, max(0.34, round(score - 0.12, 4)))
        return penalized_score, ConfidenceLevel.MEDIUM
    if confidence == ConfidenceLevel.MEDIUM:
        penalized_score = min(0.33, max(0.0, round(score - 0.12, 4)))
        return penalized_score, ConfidenceLevel.LOW
    return max(0.0, round(score - 0.08, 4)), ConfidenceLevel.LOW


def has_divergent_jurisprudence(retrieved: list[RetrievedChunk]) -> bool:
    jurisprudence = [item for item in retrieved if item.chunk.source_type.value in {"jurisprudence", "sumula"}]
    if len(jurisprudence) < 2:
        return False

    positive_markers = (
        "reconhecido",
        "cabivel",
        "dever de indenizar",
        "gera dano moral",
        "indenizavel",
        "presumido",
    )
    negative_markers = (
        "nao configurado",
        "nao automatico",
        "mero aborrecimento",
        "improcedente",
        "afastado",
        "nao gera",
    )
    positive = False
    negative = False
    for item in jurisprudence:
        content = fold_text(item.chunk.content)
        positive = positive or any(marker in content for marker in positive_markers)
        negative = negative or any(marker in content for marker in negative_markers)
    return positive and negative


def has_revoked_norm(retrieved: list[RetrievedChunk]) -> bool:
    return any(
        item.chunk.source_type.value == "legislation" and item.chunk.metadata.vigencia == "revogada"
        for item in retrieved
    )


def mixes_private_and_official_sources(retrieved: list[RetrievedChunk]) -> bool:
    has_private = any(item.chunk.source_type.value in {"user_document", "contract"} for item in retrieved)
    has_official = any(item.chunk.is_official for item in retrieved)
    return has_private and has_official
