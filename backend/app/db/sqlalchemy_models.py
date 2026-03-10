from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

try:
    from pgvector.sqlalchemy import Vector
except Exception:  # pragma: no cover
    Vector = JSON


class SourceORM(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_type: Mapped[str] = mapped_column(String(50), index=True)
    authority: Mapped[str] = mapped_column(String(20), index=True)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    url_origem: Mapped[str | None] = mapped_column(String(1000))
    hash_documento: Mapped[str | None] = mapped_column(String(128), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)


class DocumentORM(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    canonical_title: Mapped[str] = mapped_column(String(500))
    language: Mapped[str] = mapped_column(String(10), default="pt-BR")
    current_version_id: Mapped[str | None] = mapped_column(String(64), index=True)
    source = relationship("SourceORM")


class DocumentVersionORM(Base):
    __tablename__ = "document_versions"
    __table_args__ = (UniqueConstraint("document_id", "version_label", name="uq_document_version_label"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    version_label: Mapped[str] = mapped_column(String(50))
    hash_documento: Mapped[str] = mapped_column(String(128), index=True)
    raw_text: Mapped[str] = mapped_column(Text)
    vigente: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    document = relationship("DocumentORM")


class ChunkORM(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    version_id: Mapped[str] = mapped_column(ForeignKey("document_versions.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    search_vector_text: Mapped[str] = mapped_column(Text)
    hierarchy_json: Mapped[list] = mapped_column("hierarchy", JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class EmbeddingORM(Base):
    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chunk_id: Mapped[str] = mapped_column(ForeignKey("chunks.id", ondelete="CASCADE"), index=True)
    model_name: Mapped[str] = mapped_column(String(120), index=True)
    version_label: Mapped[str] = mapped_column(String(50), index=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(256))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class CitationORM(Base):
    __tablename__ = "citations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    conversation_id: Mapped[str | None] = mapped_column(ForeignKey("conversations.id", ondelete="SET NULL"), index=True)
    message_id: Mapped[str | None] = mapped_column(ForeignKey("messages.id", ondelete="SET NULL"), index=True)
    chunk_id: Mapped[str] = mapped_column(ForeignKey("chunks.id", ondelete="CASCADE"), index=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    reference_label: Mapped[str] = mapped_column(String(500))
    quote: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class RetrievalLogORM(Base):
    __tablename__ = "retrieval_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str | None] = mapped_column(ForeignKey("conversations.id", ondelete="SET NULL"), index=True)
    query_text: Mapped[str] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(50), index=True)
    filters_json: Mapped[dict] = mapped_column("filters", JSON, default=dict)
    selected_chunk_ids: Mapped[list] = mapped_column(JSON, default=list)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ConversationORM(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    channel: Mapped[str] = mapped_column(String(50), default="web")
    owner_user_id: Mapped[str | None] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class MessageORM(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20), index=True)
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class UserUploadORM(Base):
    __tablename__ = "user_uploads"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    conversation_id: Mapped[str | None] = mapped_column(ForeignKey("conversations.id", ondelete="SET NULL"), index=True)
    owner_user_id: Mapped[str | None] = mapped_column(String(64), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(120), index=True)
    file_size: Mapped[int] = mapped_column(Integer)
    storage_path: Mapped[str | None] = mapped_column(String(500))
    source_id: Mapped[str | None] = mapped_column(ForeignKey("sources.id", ondelete="SET NULL"), index=True)
    retention_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class IngestionJobORM(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    manifest_path: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), index=True, default="running")
    source_types_json: Mapped[list] = mapped_column("source_types", JSON, default=list)
    imported_sources: Mapped[int] = mapped_column(Integer, default=0)
    imported_chunks: Mapped[int] = mapped_column(Integer, default=0)
    skipped_sources: Mapped[int] = mapped_column(Integer, default=0)
    failed_sources: Mapped[int] = mapped_column(Integer, default=0)
    warnings_json: Mapped[list] = mapped_column("warnings", JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SourceSyncStateORM(Base):
    __tablename__ = "source_sync_state"

    source_key: Mapped[str] = mapped_column(String(255), primary_key=True)
    source_id: Mapped[str | None] = mapped_column(String(64), index=True)
    version_id: Mapped[str | None] = mapped_column(String(64), index=True)
    last_hash: Mapped[str | None] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True, default="pending")
    last_error: Mapped[str | None] = mapped_column(Text)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class LegalEntityORM(Base):
    __tablename__ = "legal_entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    entity_value: Mapped[str] = mapped_column(String(255), index=True)
    normalized_value: Mapped[str] = mapped_column(String(255), index=True)


class JurisprudenceMetadataORM(Base):
    __tablename__ = "jurisprudence_metadata"

    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True)
    tribunal: Mapped[str | None] = mapped_column(String(120), index=True)
    orgao_julgador: Mapped[str | None] = mapped_column(String(120), index=True)
    numero_processo: Mapped[str | None] = mapped_column(String(120), index=True)
    relator: Mapped[str | None] = mapped_column(String(120))
    data_julgamento: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    data_publicacao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    ementa: Mapped[str | None] = mapped_column(Text)
    tese: Mapped[str | None] = mapped_column(Text)


class LegislationMetadataORM(Base):
    __tablename__ = "legislation_metadata"

    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True)
    numero_norma: Mapped[str | None] = mapped_column(String(120), index=True)
    tipo_norma: Mapped[str | None] = mapped_column(String(50), index=True)
    artigo: Mapped[str | None] = mapped_column(String(50), index=True)
    vigencia: Mapped[str | None] = mapped_column(String(120), index=True)
    data_publicacao: Mapped[Date | None] = mapped_column(Date, index=True)
    uf: Mapped[str | None] = mapped_column(String(2), index=True)


class ContractsMetadataORM(Base):
    __tablename__ = "contracts_metadata"

    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True)
    contract_type: Mapped[str | None] = mapped_column(String(120), index=True)
    parties_count: Mapped[int | None] = mapped_column(Integer)
    contains_personal_data: Mapped[bool] = mapped_column(Boolean, default=False)
    contains_arbitration_clause: Mapped[bool] = mapped_column(Boolean, default=False)
