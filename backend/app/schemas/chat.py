from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from backend.app.core.enums import ResponseMode
from backend.app.models.domain import Citation


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    mode: ResponseMode = ResponseMode.FRIENDLY
    source_filters: list[str] = Field(default_factory=list)
    debug: bool = False
    conversation_id: str | None = None
    user_document_ids: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    resposta: str
    resposta_objetiva: str
    fundamentacao_juridica: str
    fontes_consultadas: list[Citation]
    citacoes: list[str]
    limites: list[str]
    proximos_passos: list[str]
    confidence_score: float
    confidence_level: str
    sufficient_support: bool
    requires_human_escalation: bool
    intent: str
    mode: str
    debug: dict[str, Any] | None = None

