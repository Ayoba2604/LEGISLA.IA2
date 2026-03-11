from datetime import datetime, timedelta

from backend.app.observability.alerts import collect_operational_alerts


class StubPersistence:
    enabled = True

    def __init__(self):
        self._now = datetime.utcnow()

    def database_status(self):
        return {
            "enabled": True,
            "connected": True,
            "pgvector_ready": True,
            "failed_sync_sources": 2,
            "expired_uploads_pending": 0,
            "running_ingestion_jobs": 1,
            "error": None,
        }

    def list_ingestion_jobs(self, *, limit=20, status=None):
        return [
            {
                "id": 99,
                "created_at": self._now - timedelta(minutes=180),
            }
        ]


def test_collect_operational_alerts_reports_failures_and_stale_jobs():
    alerts = collect_operational_alerts(
        persistence=StubPersistence(),
        metrics_snapshot={
            "counters": {
                "responses_without_citations": 3,
                "maintenance_manifest_sync_failures": 1,
            },
            "timings_ms": [],
        },
    )

    codes = {alert["code"] for alert in alerts}
    assert "failed_sync_sources" in codes
    assert "responses_without_citations" in codes
    assert "manifest_sync_failures" in codes
    assert "stale_ingestion_jobs" in codes
