from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Iterable

from backend.app.config.settings import settings
from backend.app.core.text import extract_article_number, stable_id
from backend.app.db.base import Base
from backend.app.db.sqlalchemy_models import (
    ChunkORM,
    CitationORM,
    ConversationORM,
    DocumentORM,
    DocumentVersionORM,
    EmbeddingORM,
    IngestionJobORM,
    MessageORM,
    RetrievalLogORM,
    SourceORM,
    SourceSyncStateORM,
    UserUploadORM,
)
from backend.app.models.domain import AgentResult, ChunkRecord, SourceMetadata, SourceRecord
from backend.app.retrievers.hybrid import HybridRetriever
from backend.app.schemas.chat import ChatRequest
from backend.app.schemas.retrieval import RetrievalFilters
from backend.app.security.pii import mask_pii
from backend.app.services.model_runtime import EmbeddingService

logger = logging.getLogger(__name__)


class PersistenceService:
    def __init__(self, embedding_service: EmbeddingService) -> None:
        self.embedding_service = embedding_service
        self.enabled = bool(settings.database_enabled)
        self._SessionLocal = None
        self._engine = None
        self._hybrid = HybridRetriever()

        if not self.enabled:
            return

        try:
            from sqlalchemy import create_engine, text
            from sqlalchemy.orm import sessionmaker

            self._engine = create_engine(
                settings.database_url,
                future=True,
                echo=settings.database_echo,
                pool_pre_ping=True,
            )
            with self._engine.begin() as connection:
                connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            if settings.database_auto_create:
                Base.metadata.create_all(self._engine)
            self._SessionLocal = sessionmaker(
                bind=self._engine,
                autoflush=False,
                autocommit=False,
                future=True,
                expire_on_commit=False,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning(
                "Database persistence disabled due to initialization failure.",
                extra={"extra_payload": {"error": str(exc)}},
            )
            self.enabled = False

    @contextmanager
    def session_scope(self):
        if not self.enabled or self._SessionLocal is None:
            yield None
            return
        session = self._SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def sync_source_bundle(self, source: SourceRecord, chunks: list[ChunkRecord]) -> None:
        if not self.enabled:
            return

        with self.session_scope() as session:
            if session is None:
                return

            source_obj = session.get(SourceORM, source.source_id)
            if source_obj is None:
                source_obj = SourceORM(id=source.source_id)
            source_obj.source_type = source.source_type.value
            source_obj.authority = source.authority.value
            source_obj.is_official = source.is_official
            source_obj.is_primary = source.is_primary
            source_obj.title = source.title
            source_obj.description = source.description
            source_obj.url_origem = source.metadata.url_origem
            source_obj.hash_documento = source.metadata.hash_documento
            source_obj.metadata_json = source.metadata.model_dump(mode="json")
            session.add(source_obj)

            document_obj = session.get(DocumentORM, source.document_id)
            if document_obj is None:
                document_obj = DocumentORM(id=source.document_id)
            document_obj.source_id = source.source_id
            document_obj.canonical_title = source.title
            document_obj.current_version_id = source.version_id
            session.add(document_obj)

            version_obj = session.get(DocumentVersionORM, source.version_id)
            if version_obj is None:
                version_obj = DocumentVersionORM(id=source.version_id)
                version_obj.document_id = source.document_id
                version_obj.version_label = source.metadata.versao or "v1"
                version_obj.hash_documento = source.metadata.hash_documento or stable_id(source.version_id)
                version_obj.raw_text = source.raw_text
                version_obj.vigente = source.metadata.vigencia != "revogada"
                session.add(version_obj)

            session.flush()

            existing_chunk_ids = {
                item[0]
                for item in session.query(ChunkORM.id).filter(ChunkORM.version_id == source.version_id).all()
            }
            pending_embeddings = []
            for index, chunk in enumerate(chunks):
                if chunk.chunk_id in existing_chunk_ids:
                    continue
                chunk_obj = ChunkORM(
                    id=chunk.chunk_id,
                    source_id=chunk.source_id,
                    document_id=chunk.document_id,
                    version_id=chunk.version_id,
                    chunk_index=index,
                    title=chunk.title,
                    content=chunk.content,
                    search_vector_text=chunk.search_text,
                    hierarchy_json=chunk.hierarchy,
                    metadata_json=chunk.metadata.model_dump(mode="json"),
                )
                session.add(chunk_obj)
                pending_embeddings.append(
                    EmbeddingORM(
                        chunk_id=chunk.chunk_id,
                        model_name=self.embedding_service.model_name,
                        version_label="current",
                        embedding=chunk.embedding,
                    )
                )
            session.flush()
            for embedding in pending_embeddings:
                session.add(embedding)

    def hybrid_search(self, query: str, filters: RetrievalFilters, top_k: int) -> list:
        if not self.enabled:
            return []

        try:
            from sqlalchemy import Float, case, desc, func, literal, literal_column, select
        except Exception:  # pragma: no cover
            return []

        query_embedding = self.embedding_service.embed_query(query)
        article_number = extract_article_number(query)

        with self.session_scope() as session:
            if session is None:
                return []

            try:
                regconfig = literal_column("'portuguese'::regconfig")
                lexical_rank = func.ts_rank_cd(
                    func.to_tsvector(regconfig, ChunkORM.search_vector_text),
                    func.plainto_tsquery(regconfig, query),
                )
                article_match = literal(0.0)
                if article_number:
                    article_regex = rf"(^|[^0-9A-Za-z])art(igo)?\.?[[:space:]]*{article_number}([^0-9]|$)"
                    article_match = case(
                        (ChunkORM.search_vector_text.op("~*")(article_regex), 1.0),
                        else_=0.0,
                    )
                    lexical_rank = lexical_rank + article_match
                vector_score = (1 - EmbeddingORM.embedding.cosine_distance(query_embedding)).cast(Float)
                stmt = (
                    select(
                        ChunkORM,
                        SourceORM,
                        vector_score.label("vector_score"),
                        lexical_rank.label("lexical_score"),
                        article_match.label("article_match"),
                    )
                    .join(SourceORM, SourceORM.id == ChunkORM.source_id)
                    .join(EmbeddingORM, EmbeddingORM.chunk_id == ChunkORM.id)
                )
                stmt = self._apply_filters(stmt, filters)
                stmt = stmt.where(EmbeddingORM.model_name == self.embedding_service.model_name)
                stmt = stmt.where(EmbeddingORM.version_label == "current")
                if article_number and (not filters.source_types or "legislation" in filters.source_types):
                    stmt = stmt.order_by(desc("article_match"), desc("lexical_score"), desc("vector_score"))
                else:
                    stmt = stmt.order_by(desc("vector_score"), desc("lexical_score"))
                stmt = stmt.limit(max(settings.retrieval_candidate_limit, top_k * 8))
                rows = session.execute(stmt).all()
            except Exception as exc:  # pragma: no cover
                logger.warning(
                    "Database hybrid search failed, falling back to memory.",
                    extra={"extra_payload": {"error": str(exc)}},
                )
                return []

        ranked = []
        for row in rows:
            chunk_row, source_row, vector_value, lexical_value, _article_match = row
            metadata = SourceMetadata.model_validate(chunk_row.metadata_json or {})
            if filters.owner_user_id and metadata.metadata_extra.get("owner_user_id") != filters.owner_user_id:
                continue
            chunk = ChunkRecord(
                chunk_id=chunk_row.id,
                source_id=chunk_row.source_id,
                document_id=chunk_row.document_id,
                version_id=chunk_row.version_id,
                title=chunk_row.title,
                content=chunk_row.content,
                hierarchy=chunk_row.hierarchy_json or [],
                source_type=source_row.source_type,
                authority=source_row.authority,
                is_official=source_row.is_official,
                is_primary=source_row.is_primary,
                metadata=metadata,
                hash=stable_id(chunk_row.id, chunk_row.content),
                embedding=[],
                search_text=chunk_row.search_vector_text,
            )
            ranked.append(
                self._hybrid.build_scored_result(
                    query=query,
                    chunk=chunk,
                    vector_score=float(vector_value or 0.0),
                    lexical_score=float(lexical_value or 0.0),
                )
            )

        ranked.sort(key=lambda item: item.final_score, reverse=True)
        return self._hybrid.select_diverse(query, ranked[: settings.retrieval_candidate_limit], top_k)

    def log_chat_turn(
        self,
        request: ChatRequest,
        result: AgentResult,
        *,
        latency_ms: float = 0.0,
        llm_backend: str = "unknown",
        user_id: str | None = None,
    ) -> None:
        if not self.enabled:
            return

        with self.session_scope() as session:
            if session is None:
                return

            conversation_id = request.conversation_id or stable_id("conversation", request.question[:120])
            conversation = session.get(ConversationORM, conversation_id)
            if conversation is None:
                conversation = ConversationORM(id=conversation_id, channel="web", owner_user_id=user_id)
                session.add(conversation)
            conversation.updated_at = datetime.utcnow()
            if user_id and not conversation.owner_user_id:
                conversation.owner_user_id = user_id

            user_message_id = stable_id(conversation_id, "user", request.question[:120])
            assistant_message_id = stable_id(conversation_id, "assistant", result.answer.resposta_objetiva[:120])

            session.merge(
                MessageORM(
                    id=user_message_id,
                    conversation_id=conversation_id,
                    role="user",
                    content=request.question,
                    token_count=len(request.question.split()),
                )
            )
            session.merge(
                MessageORM(
                    id=assistant_message_id,
                    conversation_id=conversation_id,
                    role="assistant",
                    content=result.answer.resposta_objetiva,
                    token_count=len(result.answer.resposta_objetiva.split()),
                    cost_usd=0.0,
                )
            )
            session.flush()
            session.add(
                RetrievalLogORM(
                    conversation_id=conversation_id,
                    query_text=request.question,
                    intent=result.intent.value,
                    filters_json={
                        "source_filters": request.source_filters,
                        "llm_backend": llm_backend,
                    },
                    selected_chunk_ids=[item.chunk.chunk_id for item in result.retrieved_chunks],
                    confidence_score=result.confidence_score,
                    latency_ms=latency_ms,
                )
            )
            for citation in result.answer.fontes_consultadas:
                session.merge(
                    CitationORM(
                        id=stable_id(assistant_message_id, citation.chunk_id, citation.reference_label),
                        conversation_id=conversation_id,
                        message_id=assistant_message_id,
                        chunk_id=citation.chunk_id,
                        source_id=citation.source_id,
                        reference_label=citation.reference_label,
                        quote=citation.quote,
                    )
                )

    def record_upload(
        self,
        *,
        conversation_id: str | None,
        filename: str,
        mime_type: str,
        file_size: int,
        source_id: str,
        owner_user_id: str | None = None,
        retention_expires_at: datetime | None = None,
    ) -> None:
        if not self.enabled:
            return

        with self.session_scope() as session:
            if session is None:
                return
            upload_id = stable_id(filename, source_id, str(file_size))
            session.merge(
                UserUploadORM(
                    id=upload_id,
                    conversation_id=conversation_id,
                    owner_user_id=owner_user_id,
                    filename=filename,
                    mime_type=mime_type,
                    file_size=file_size,
                    source_id=source_id,
                    retention_expires_at=retention_expires_at,
                )
            )

    def start_ingestion_job(self, *, manifest_path: str, source_types: list[str]) -> int | None:
        if not self.enabled:
            return None

        with self.session_scope() as session:
            if session is None:
                return None
            job = IngestionJobORM(
                manifest_path=manifest_path,
                status="running",
                source_types_json=source_types,
            )
            session.add(job)
            session.flush()
            return job.id

    def finish_ingestion_job(
        self,
        job_id: int | None,
        *,
        status: str,
        imported_sources: int,
        imported_chunks: int,
        skipped_sources: int,
        failed_sources: int,
        warnings: list[str],
    ) -> None:
        if not self.enabled or job_id is None:
            return

        with self.session_scope() as session:
            if session is None:
                return
            job = session.get(IngestionJobORM, job_id)
            if job is None:
                return
            job.status = status
            job.imported_sources = imported_sources
            job.imported_chunks = imported_chunks
            job.skipped_sources = skipped_sources
            job.failed_sources = failed_sources
            job.warnings_json = warnings
            job.finished_at = datetime.utcnow()

    def get_sync_state(self, source_key: str) -> dict | None:
        if not self.enabled:
            return None

        with self.session_scope() as session:
            if session is None:
                return None
            state = session.get(SourceSyncStateORM, source_key)
            if state is None:
                return None
            return {
                "source_key": state.source_key,
                "source_id": state.source_id,
                "version_id": state.version_id,
                "last_hash": state.last_hash,
                "status": state.status,
            }

    def upsert_sync_state(
        self,
        *,
        source_key: str,
        source_id: str | None,
        version_id: str | None,
        last_hash: str | None,
        status: str,
        last_error: str | None = None,
    ) -> None:
        if not self.enabled:
            return

        with self.session_scope() as session:
            if session is None:
                return
            state = session.get(SourceSyncStateORM, source_key)
            if state is None:
                state = SourceSyncStateORM(source_key=source_key)
            state.source_id = source_id
            state.version_id = version_id
            state.last_hash = last_hash
            state.status = status
            state.last_error = last_error
            state.last_synced_at = datetime.utcnow()
            session.add(state)

    def database_status(self) -> dict:
        status = {
            "enabled": self.enabled,
            "connected": False,
            "pgvector_ready": False,
            "failed_sync_sources": 0,
            "expired_uploads_pending": 0,
            "running_ingestion_jobs": 0,
            "error": None,
        }
        if not self.enabled:
            return status

        try:
            from sqlalchemy import text

            with self.session_scope() as session:
                if session is None:
                    return status
                session.execute(text("SELECT 1"))
                status["connected"] = True
                status["pgvector_ready"] = bool(
                    session.execute(text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")).scalar()
                )
                status["failed_sync_sources"] = (
                    session.query(SourceSyncStateORM).filter(SourceSyncStateORM.status == "failed").count()
                )
                status["expired_uploads_pending"] = (
                    session.query(UserUploadORM)
                    .filter(
                        UserUploadORM.retention_expires_at.is_not(None),
                        UserUploadORM.retention_expires_at <= datetime.utcnow(),
                        UserUploadORM.deleted_at.is_(None),
                    )
                    .count()
                )
                status["running_ingestion_jobs"] = (
                    session.query(IngestionJobORM).filter(IngestionJobORM.status == "running").count()
                )
        except Exception as exc:  # pragma: no cover
            status["error"] = str(exc)

        return status

    def list_ingestion_jobs(self, *, limit: int = 20, status: str | None = None) -> list[dict]:
        if not self.enabled:
            return []

        with self.session_scope() as session:
            if session is None:
                return []
            query = session.query(IngestionJobORM)
            if status:
                query = query.filter(IngestionJobORM.status == status)
            rows = query.order_by(IngestionJobORM.created_at.desc()).limit(limit).all()
            return [
                {
                    "id": row.id,
                    "manifest_path": row.manifest_path,
                    "status": row.status,
                    "source_types": row.source_types_json or [],
                    "imported_sources": row.imported_sources,
                    "imported_chunks": row.imported_chunks,
                    "skipped_sources": row.skipped_sources,
                    "failed_sources": row.failed_sources,
                    "warnings": row.warnings_json or [],
                    "created_at": row.created_at,
                    "finished_at": row.finished_at,
                }
                for row in rows
            ]

    def list_sync_states(self, *, limit: int = 50, status: str | None = None) -> list[dict]:
        if not self.enabled:
            return []

        with self.session_scope() as session:
            if session is None:
                return []
            query = session.query(SourceSyncStateORM)
            if status:
                query = query.filter(SourceSyncStateORM.status == status)
            rows = query.order_by(SourceSyncStateORM.last_synced_at.desc()).limit(limit).all()
            return [
                {
                    "source_key": row.source_key,
                    "source_id": row.source_id,
                    "version_id": row.version_id,
                    "last_hash": row.last_hash,
                    "status": row.status,
                    "last_error": row.last_error,
                    "last_synced_at": row.last_synced_at,
                }
                for row in rows
            ]

    def list_recent_retrievals(
        self,
        *,
        limit: int = 50,
        conversation_id: str | None = None,
        owner_user_id: str | None = None,
    ) -> list[dict]:
        if not self.enabled:
            return []

        with self.session_scope() as session:
            if session is None:
                return []
            query = session.query(RetrievalLogORM, ConversationORM.owner_user_id).outerjoin(
                ConversationORM, ConversationORM.id == RetrievalLogORM.conversation_id
            )
            if conversation_id:
                query = query.filter(RetrievalLogORM.conversation_id == conversation_id)
            if owner_user_id:
                query = query.filter(ConversationORM.owner_user_id == owner_user_id)
            rows = query.order_by(RetrievalLogORM.created_at.desc()).limit(limit).all()
            return [
                {
                    "id": retrieval.id,
                    "conversation_id": retrieval.conversation_id,
                    "owner_user_id": conversation_owner,
                    "query_text": mask_pii(retrieval.query_text),
                    "intent": retrieval.intent,
                    "confidence_score": retrieval.confidence_score,
                    "latency_ms": retrieval.latency_ms,
                    "selected_chunk_ids": retrieval.selected_chunk_ids or [],
                    "filters": retrieval.filters_json or {},
                    "created_at": retrieval.created_at,
                }
                for retrieval, conversation_owner in rows
            ]

    def list_uploads(
        self,
        *,
        limit: int = 50,
        owner_user_id: str | None = None,
        include_deleted: bool = False,
    ) -> list[dict]:
        if not self.enabled:
            return []

        with self.session_scope() as session:
            if session is None:
                return []
            query = session.query(UserUploadORM)
            if owner_user_id:
                query = query.filter(UserUploadORM.owner_user_id == owner_user_id)
            if not include_deleted:
                query = query.filter(UserUploadORM.deleted_at.is_(None))
            rows = query.order_by(UserUploadORM.created_at.desc()).limit(limit).all()
            return [
                {
                    "id": row.id,
                    "conversation_id": row.conversation_id,
                    "owner_user_id": row.owner_user_id,
                    "filename": row.filename,
                    "mime_type": row.mime_type,
                    "file_size": row.file_size,
                    "source_id": row.source_id,
                    "retention_expires_at": row.retention_expires_at,
                    "deleted_at": row.deleted_at,
                    "created_at": row.created_at,
                }
                for row in rows
            ]

    def cleanup_expired_uploads(
        self,
        *,
        limit: int = 200,
        hard_delete: bool = False,
        now: datetime | None = None,
    ) -> dict:
        report = {
            "processed_uploads": 0,
            "purged_sources": 0,
            "hard_deleted_uploads": 0,
            "soft_deleted_uploads": 0,
            "source_ids": [],
        }
        if not self.enabled:
            return report

        now = now or datetime.utcnow()
        source_ids: list[str] = []
        seen_source_ids: set[str] = set()

        with self.session_scope() as session:
            if session is None:
                return report
            query = session.query(UserUploadORM).filter(
                UserUploadORM.retention_expires_at.is_not(None),
                UserUploadORM.retention_expires_at <= now,
            )
            if not hard_delete:
                query = query.filter(UserUploadORM.deleted_at.is_(None))
            uploads = query.order_by(UserUploadORM.retention_expires_at.asc()).limit(limit).all()

            for upload in uploads:
                report["processed_uploads"] += 1
                source_id = upload.source_id
                if source_id and source_id not in seen_source_ids:
                    source = session.get(SourceORM, source_id)
                    if source is not None:
                        session.delete(source)
                        seen_source_ids.add(source_id)
                        source_ids.append(source_id)
                        report["purged_sources"] += 1
                if hard_delete:
                    session.delete(upload)
                    report["hard_deleted_uploads"] += 1
                else:
                    upload.deleted_at = now
                    upload.storage_path = None
                    upload.source_id = None
                    report["soft_deleted_uploads"] += 1

        report["source_ids"] = source_ids
        return report

    def purge_corpus(self) -> int:
        if not self.enabled:
            return 0

        with self.session_scope() as session:
            if session is None:
                return 0
            deleted_sources = session.query(SourceORM).count()
            session.query(SourceSyncStateORM).delete(synchronize_session=False)
            session.query(EmbeddingORM).delete(synchronize_session=False)
            session.query(ChunkORM).delete(synchronize_session=False)
            session.query(DocumentVersionORM).delete(synchronize_session=False)
            session.query(DocumentORM).delete(synchronize_session=False)
            session.query(SourceORM).delete(synchronize_session=False)
            return deleted_sources

    @staticmethod
    def _apply_filters(stmt, filters: RetrievalFilters):
        if filters.source_types:
            stmt = stmt.where(SourceORM.source_type.in_(filters.source_types))
        if filters.source_ids:
            stmt = stmt.where(ChunkORM.source_id.in_(filters.source_ids))
        if filters.only_official:
            stmt = stmt.where(SourceORM.is_official.is_(True))
        if filters.only_user_documents:
            stmt = stmt.where(SourceORM.source_type == "user_document")
        if filters.tribunal:
            stmt = stmt.where(ChunkORM.metadata_json["tribunal"].astext == filters.tribunal)
        if filters.orgao_julgador:
            stmt = stmt.where(ChunkORM.metadata_json["orgao_julgador"].astext == filters.orgao_julgador)
        if filters.relator:
            stmt = stmt.where(ChunkORM.metadata_json["relator"].astext == filters.relator)
        if filters.numero_processo:
            stmt = stmt.where(ChunkORM.metadata_json["numero_processo"].astext == filters.numero_processo)
        if filters.numero_norma:
            stmt = stmt.where(ChunkORM.metadata_json["numero_norma"].astext == filters.numero_norma)
        if filters.artigo:
            stmt = stmt.where(ChunkORM.metadata_json["artigo"].astext == filters.artigo)
        if filters.tema:
            stmt = stmt.where(ChunkORM.metadata_json["tema"].astext == filters.tema)
        if filters.uf:
            stmt = stmt.where(ChunkORM.metadata_json["uf"].astext == filters.uf)
        if filters.ramo_direito:
            stmt = stmt.where(ChunkORM.metadata_json["ramo_direito"].astext == filters.ramo_direito)
        return stmt
