from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if not raw:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


class RetrievalWeights(BaseModel):
    vector: float = 0.35
    lexical: float = 0.30
    official_priority: float = 0.15
    recency: float = 0.05
    source_type: float = 0.10
    rerank: float = 0.05


class Settings(BaseModel):
    app_name: str = "Legisla.IA Legal RAG API"
    app_version: str = "2.0.0"
    environment: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    debug: bool = Field(default_factory=lambda: _env_bool("APP_DEBUG", True))
    host: str = Field(default_factory=lambda: os.getenv("APP_HOST", "0.0.0.0"))
    port: int = Field(default_factory=lambda: int(os.getenv("APP_PORT", "8000")))
    api_prefix: str = "/api/v1"
    expose_debug_trace: bool = Field(default_factory=lambda: _env_bool("EXPOSE_DEBUG_TRACE", True))
    cors_origins: list[str] = Field(
        default_factory=lambda: _env_list(
            "CORS_ORIGINS",
            [
                "http://localhost",
                "http://127.0.0.1",
                "http://localhost:8080",
                "http://127.0.0.1:8080",
            ],
        )
    )
    admin_token: str = Field(default_factory=lambda: os.getenv("LEGISLA_ADMIN_TOKEN", "change-me"))
    internal_service_secret: str = Field(default_factory=lambda: os.getenv("LEGISLA_INTERNAL_SECRET", "change-me-internal"))
    require_chat_auth: bool = Field(default_factory=lambda: _env_bool("REQUIRE_CHAT_AUTH", False))
    user_token_ttl_seconds: int = Field(default_factory=lambda: int(os.getenv("USER_TOKEN_TTL_SECONDS", "900")))
    user_upload_retention_days: int = Field(default_factory=lambda: int(os.getenv("USER_UPLOAD_RETENTION_DAYS", "30")))
    llm_provider: str = Field(default_factory=lambda: os.getenv("LLM_PROVIDER", "mock"))
    llm_model: str = Field(default_factory=lambda: os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"))
    use_langgraph_agent: bool = Field(default_factory=lambda: _env_bool("USE_LANGGRAPH_AGENT", True))
    embedding_provider: str = Field(default_factory=lambda: os.getenv("EMBEDDING_PROVIDER", "hash"))
    embedding_model: str = Field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))
    reranker_provider: str = Field(default_factory=lambda: os.getenv("RERANKER_PROVIDER", "heuristic"))
    reranker_model: str = Field(
        default_factory=lambda: os.getenv("RERANKER_MODEL", "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
    )
    reranker_blend_weight: float = Field(default_factory=lambda: float(os.getenv("RERANKER_BLEND_WEIGHT", "0.25")))
    reranker_candidate_limit: int = Field(default_factory=lambda: int(os.getenv("RERANKER_CANDIDATE_LIMIT", "12")))
    openai_api_key: str | None = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    groq_api_key: str | None = Field(default_factory=lambda: os.getenv("GROQ_API_KEY"))
    database_url: str | None = Field(default_factory=lambda: os.getenv("DATABASE_URL"))
    database_auto_create: bool = Field(default_factory=lambda: _env_bool("DATABASE_AUTO_CREATE", True))
    database_echo: bool = Field(default_factory=lambda: _env_bool("DATABASE_ECHO", False))
    persist_bootstrap_to_db: bool = Field(default_factory=lambda: _env_bool("PERSIST_BOOTSTRAP_TO_DB", True))
    bootstrap_manifest_path: Path = Field(
        default_factory=lambda: Path(
            os.getenv(
                "BOOTSTRAP_MANIFEST_PATH",
                str(Path(__file__).resolve().parents[2] / "data" / "bootstrap" / "corpus_manifest.json"),
            )
        )
    )
    enable_legacy_bootstrap_fallback: bool = Field(
        default_factory=lambda: _env_bool("ENABLE_LEGACY_BOOTSTRAP_FALLBACK", True)
    )
    official_corpus_registry_path: Path = Field(
        default_factory=lambda: Path(
            os.getenv(
                "OFFICIAL_CORPUS_REGISTRY_PATH",
                str(Path(__file__).resolve().parents[2] / "data" / "bootstrap" / "official_corpus_registry.json"),
            )
        )
    )
    official_corpus_manifest_output_path: Path = Field(
        default_factory=lambda: Path(
            os.getenv(
                "OFFICIAL_CORPUS_MANIFEST_OUTPUT_PATH",
                str(Path(__file__).resolve().parents[2] / "data" / "bootstrap" / "corpus_manifest.official.json"),
            )
        )
    )
    official_corpus_snapshot_dir: Path = Field(
        default_factory=lambda: Path(
            os.getenv(
                "OFFICIAL_CORPUS_SNAPSHOT_DIR",
                str(Path(__file__).resolve().parents[2] / "data" / "corpus_snapshots" / "official"),
            )
        )
    )
    ingest_http_timeout_seconds: float = Field(
        default_factory=lambda: float(os.getenv("INGEST_HTTP_TIMEOUT_SECONDS", "20"))
    )
    ingest_http_max_retries: int = Field(default_factory=lambda: int(os.getenv("INGEST_HTTP_MAX_RETRIES", "2")))
    ingest_http_verify_ssl: bool = Field(default_factory=lambda: _env_bool("INGEST_HTTP_VERIFY_SSL", True))
    maintenance_scheduler_enabled: bool = Field(
        default_factory=lambda: _env_bool("MAINTENANCE_SCHEDULER_ENABLED", False)
    )
    maintenance_auto_sync_on_startup: bool = Field(
        default_factory=lambda: _env_bool("MAINTENANCE_AUTO_SYNC_ON_STARTUP", False)
    )
    maintenance_cleanup_interval_seconds: int = Field(
        default_factory=lambda: int(os.getenv("MAINTENANCE_CLEANUP_INTERVAL_SECONDS", "900"))
    )
    maintenance_sync_interval_seconds: int = Field(
        default_factory=lambda: int(os.getenv("MAINTENANCE_SYNC_INTERVAL_SECONDS", "3600"))
    )
    maintenance_cleanup_batch_size: int = Field(
        default_factory=lambda: int(os.getenv("MAINTENANCE_CLEANUP_BATCH_SIZE", "200"))
    )
    langsmith_tracing: bool = Field(default_factory=lambda: _env_bool("LANGSMITH_TRACING", False))
    langsmith_api_key: str | None = Field(default_factory=lambda: os.getenv("LANGSMITH_API_KEY"))
    langsmith_project: str | None = Field(default_factory=lambda: os.getenv("LANGSMITH_PROJECT"))
    datajud_api_key: str | None = Field(default_factory=lambda: os.getenv("DATAJUD_API_KEY"))
    datajud_api_header_name: str = Field(default_factory=lambda: os.getenv("DATAJUD_API_HEADER_NAME", "Authorization"))
    datajud_api_header_prefix: str = Field(default_factory=lambda: os.getenv("DATAJUD_API_HEADER_PREFIX", "ApiKey "))
    retrieval_top_k: int = Field(default_factory=lambda: int(os.getenv("RETRIEVAL_TOP_K", "6")))
    retrieval_candidate_limit: int = Field(default_factory=lambda: int(os.getenv("RETRIEVAL_CANDIDATE_LIMIT", "20")))
    retrieval_mmr_lambda: float = Field(default_factory=lambda: float(os.getenv("RETRIEVAL_MMR_LAMBDA", "0.75")))
    retrieval_backend: str = Field(default_factory=lambda: os.getenv("RETRIEVAL_BACKEND", "auto"))
    retrieval_weights: RetrievalWeights = Field(default_factory=RetrievalWeights)
    max_upload_bytes: int = Field(default_factory=lambda: int(os.getenv("MAX_UPLOAD_BYTES", str(8 * 1024 * 1024))))
    allowed_upload_mime_types: list[str] = Field(
        default_factory=lambda: _env_list(
            "ALLOWED_UPLOAD_MIME_TYPES",
            [
                "application/pdf",
                "text/plain",
                "text/markdown",
                "application/json",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ],
        )
    )
    rate_limit_requests_per_minute: int = Field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
    )
    root_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[3])
    legacy_data_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[3] / "IA" / "data")
    bootstrap_data_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2] / "data" / "bootstrap"
    )

    def source_type_priority(self, source_type: str) -> float:
        mapping = {
            "legislation": 1.0,
            "jurisprudence": 0.95,
            "sumula": 0.92,
            "process_metadata": 0.88,
            "licensed_doctrine": 0.7,
            "user_document": 0.85,
            "contract": 0.75,
            "situation": 0.65,
            "legacy_seed": 0.5,
        }
        return mapping.get(source_type, 0.5)

    @property
    def database_enabled(self) -> bool:
        return bool(self.database_url)

    def dict_for_debug(self) -> dict[str, Any]:
        data = self.model_dump()
        for secret_name in ("admin_token", "internal_service_secret", "openai_api_key", "groq_api_key", "database_url"):
            if data.get(secret_name):
                data[secret_name] = "***"
        return data


settings = Settings()
