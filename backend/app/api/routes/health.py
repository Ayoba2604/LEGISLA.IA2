from fastapi import APIRouter, Request

from backend.app.config.settings import settings
from backend.app.observability.metrics import metrics

router = APIRouter(tags=["health"])


@router.get("/health")
@router.get(f"{settings.api_prefix}/health")
def health(request: Request):
    catalog = getattr(request.app.state, "catalog", None)
    chat_service = getattr(request.app.state, "chat_service", None)
    persistence = getattr(request.app.state, "persistence", None)
    database_status = persistence.database_status() if persistence else {"enabled": False, "connected": False, "pgvector_ready": False}
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "retrieval_backend": settings.retrieval_backend,
        "database_enabled": bool(persistence and persistence.enabled),
        "database": database_status,
        "embedding_backend": request.app.state.embedding_service.active_backend if getattr(request.app.state, "embedding_service", None) else "unknown",
        "reranker_backend": request.app.state.reranker_service.active_backend if getattr(request.app.state, "reranker_service", None) else "unknown",
        "llm_backend": chat_service.llm_service.active_backend if chat_service else "unknown",
        "langgraph_enabled": settings.use_langgraph_agent,
        "langsmith_tracing": settings.langsmith_tracing,
        "manifest_path": str(settings.bootstrap_manifest_path),
        "manifest_present": settings.bootstrap_manifest_path.exists(),
        "sources_loaded": len(catalog.sources) if catalog else 0,
        "chunks_loaded": len(catalog.chunks) if catalog else 0,
        "metrics": metrics.snapshot(),
    }
