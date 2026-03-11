from __future__ import annotations

from datetime import datetime, timedelta

from backend.app.config.settings import settings


def collect_operational_alerts(*, persistence=None, metrics_snapshot: dict | None = None) -> list[dict]:
    metrics_snapshot = metrics_snapshot or {"counters": {}, "timings_ms": []}
    counters = metrics_snapshot.get("counters", {}) or {}
    alerts: list[dict] = []

    database_status = (
        persistence.database_status()
        if persistence is not None and getattr(persistence, "enabled", False)
        else {"enabled": False, "connected": False, "pgvector_ready": False, "error": None}
    )

    if database_status.get("error"):
        alerts.append(
            {
                "code": "database_unavailable",
                "severity": "critical",
                "message": "Persistencia PostgreSQL/pgvector indisponivel para o backend.",
                "context": {"error": database_status.get("error")},
            }
        )

    if database_status.get("failed_sync_sources", 0) >= settings.alert_failed_sync_sources_threshold:
        alerts.append(
            {
                "code": "failed_sync_sources",
                "severity": "warning",
                "message": "Ha fontes com falha de sincronizacao no pipeline oficial.",
                "context": {"failed_sync_sources": database_status.get("failed_sync_sources", 0)},
            }
        )

    if counters.get("responses_without_citations", 0) >= settings.alert_responses_without_citation_threshold:
        alerts.append(
            {
                "code": "responses_without_citations",
                "severity": "warning",
                "message": "O sistema respondeu sem citacoes verificaveis acima do limiar configurado.",
                "context": {"responses_without_citations": counters.get("responses_without_citations", 0)},
            }
        )

    if counters.get("maintenance_manifest_sync_failures", 0):
        alerts.append(
            {
                "code": "manifest_sync_failures",
                "severity": "warning",
                "message": "Foram registradas falhas de sincronizacao do manifesto oficial.",
                "context": {"maintenance_manifest_sync_failures": counters.get("maintenance_manifest_sync_failures", 0)},
            }
        )

    if persistence is not None and getattr(persistence, "enabled", False):
        running_jobs = persistence.list_ingestion_jobs(limit=20, status="running")
        cutoff = datetime.utcnow() - timedelta(minutes=settings.alert_stale_ingestion_job_minutes)
        stale_jobs = [
            {"id": job["id"], "created_at": job["created_at"].isoformat() if job.get("created_at") else None}
            for job in running_jobs
            if job.get("created_at") and job["created_at"].replace(tzinfo=None) < cutoff
        ]
        if stale_jobs:
            alerts.append(
                {
                    "code": "stale_ingestion_jobs",
                    "severity": "warning",
                    "message": "Ha jobs de ingestao em execucao alem do tempo esperado.",
                    "context": {"jobs": stale_jobs},
                }
            )

    return alerts
