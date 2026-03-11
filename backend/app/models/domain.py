from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from backend.app.core.enums import ConfidenceLevel, IntentType, ResponseMode, SourceAuthority, SourceType


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SourceMetadata(BaseModel):
    tribunal: str | None = None
    orgao_julgador: str | None = None
    numero_processo: str | None = None
    numero_norma: str | None = None
    parte: str | None = None
    livro: str | None = None
    titulo_normativo: str | None = None
    capitulo: str | None = None
    secao: str | None = None
    subsecao: str | None = None
    artigo: str | None = None
    paragrafo: str | None = None
    inciso: str | None = None
    alinea: str | None = None
    sumula_numero: str | None = None
    enunciado: str | None = None
    tese_juridica: str | None = None
    dispositivo: str | None = None
    relator: str | None = None
    data_publicacao: date | None = None
    data_julgamento: date | None = None
    uf: str | None = None
    ramo_direito: str | None = None
    tema: str | None = None
    url_origem: str | None = None
    hash_documento: str | None = None
    versao: str | None = None
    vigencia: str | None = None
    metadata_extra: dict[str, Any] = Field(default_factory=dict)


class SourceRecord(BaseModel):
    source_id: str
    document_id: str
    version_id: str
    title: str
    source_type: SourceType
    authority: SourceAuthority
    is_official: bool = False
    is_primary: bool = False
    description: str = ""
    raw_text: str = ""
    hierarchy: list[str] = Field(default_factory=list)
    metadata: SourceMetadata = Field(default_factory=SourceMetadata)
    created_at: datetime = Field(default_factory=utcnow)


class ChunkRecord(BaseModel):
    chunk_id: str
    source_id: str
    document_id: str
    version_id: str
    title: str
    content: str
    hierarchy: list[str] = Field(default_factory=list)
    source_type: SourceType
    authority: SourceAuthority
    is_official: bool = False
    is_primary: bool = False
    metadata: SourceMetadata = Field(default_factory=SourceMetadata)
    hash: str
    embedding: list[float] = Field(default_factory=list)
    search_text: str = ""


class Citation(BaseModel):
    citation_id: str
    chunk_id: str
    source_id: str
    title: str
    source_type: SourceType
    authority: SourceAuthority
    quote: str
    reference_label: str
    url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievedChunk(BaseModel):
    chunk: ChunkRecord
    vector_score: float
    lexical_score: float
    rerank_score: float
    final_score: float
    reason: str


class ToolCallTrace(BaseModel):
    tool_name: str
    input_payload: dict[str, Any] = Field(default_factory=dict)
    summary: str = ""


class DebugTrace(BaseModel):
    query: str
    mode: ResponseMode
    intent: IntentType
    tools_called: list[ToolCallTrace] = Field(default_factory=list)
    retrieved_chunks: list[dict[str, Any]] = Field(default_factory=list)
    reranked_chunks: list[dict[str, Any]] = Field(default_factory=list)
    final_context: list[dict[str, Any]] = Field(default_factory=list)
    response_preview: str = ""
    confidence_score: float = 0.0


class AnswerSections(BaseModel):
    resposta_objetiva: str
    fundamentacao_juridica: str
    fontes_consultadas: list[Citation]
    citacoes: list[str]
    limites: list[str]
    proximos_passos: list[str]


class AgentResult(BaseModel):
    answer: AnswerSections
    confidence_score: float
    confidence_level: ConfidenceLevel
    intent: IntentType
    mode: ResponseMode
    sufficient_support: bool
    requires_human_escalation: bool
    debug: DebugTrace | None = None
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    tool_traces: list[ToolCallTrace] = Field(default_factory=list)
