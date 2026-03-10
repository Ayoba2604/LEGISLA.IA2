from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from backend.app.config.settings import settings
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.observability.metrics import metrics
from backend.app.observability.tracing import trace_step
from backend.app.schemas.admin import CleanupExpiredUploadsReport
from backend.app.services.source_catalog import SourceCatalog

logger = logging.getLogger(__name__)


class MaintenanceService:
    def __init__(self, *, persistence=None, ingestion_pipeline: IngestionPipeline | None = None) -> None:
        self.persistence = persistence
        self.ingestion_pipeline = ingestion_pipeline or IngestionPipeline()

    def sync_manifest(
        self,
        *,
        catalog: SourceCatalog,
        manifest_path: Path | None = None,
        persist: bool = True,
        source_types=None,
    ):
        manifest = manifest_path or settings.bootstrap_manifest_path
        if not manifest.exists():
            raise FileNotFoundError(f"Manifesto nao encontrado: {manifest}")

        with trace_step("maintenance.sync_manifest"):
            report = self.ingestion_pipeline.ingest_manifest(
                manifest_path=manifest,
                catalog=catalog,
                persist=persist,
                source_types=source_types,
            )
        metrics.incr("maintenance_manifest_sync_runs")
        if report.failed_sources:
            metrics.incr("maintenance_manifest_sync_failures")
        return report

    def cleanup_expired_uploads(
        self,
        *,
        catalog: SourceCatalog,
        limit: int | None = None,
        hard_delete: bool = False,
    ) -> CleanupExpiredUploadsReport:
        if not self.persistence or not self.persistence.enabled:
            return CleanupExpiredUploadsReport(
                processed_uploads=0,
                purged_sources=0,
                removed_chunks=0,
                hard_deleted_uploads=0,
                soft_deleted_uploads=0,
                source_ids=[],
                warnings=["Persistencia desabilitada; nenhuma limpeza foi executada."],
            )

        with trace_step("maintenance.cleanup_expired_uploads"):
            raw_report = self.persistence.cleanup_expired_uploads(
                limit=limit or settings.maintenance_cleanup_batch_size,
                hard_delete=hard_delete,
            )

        removed_chunks = 0
        for source_id in raw_report["source_ids"]:
            removed_chunks += catalog.remove_source(source_id)

        metrics.incr("maintenance_cleanup_runs")
        if raw_report["processed_uploads"]:
            metrics.incr("maintenance_expired_uploads_processed", raw_report["processed_uploads"])
        if raw_report["purged_sources"]:
            metrics.incr("maintenance_sources_purged", raw_report["purged_sources"])

        return CleanupExpiredUploadsReport(
            processed_uploads=raw_report["processed_uploads"],
            purged_sources=raw_report["purged_sources"],
            removed_chunks=removed_chunks,
            hard_deleted_uploads=raw_report["hard_deleted_uploads"],
            soft_deleted_uploads=raw_report["soft_deleted_uploads"],
            source_ids=raw_report["source_ids"],
            warnings=[],
        )


class MaintenanceScheduler:
    def __init__(self, maintenance_service: MaintenanceService, catalog: SourceCatalog) -> None:
        self.maintenance_service = maintenance_service
        self.catalog = catalog
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        if not settings.maintenance_scheduler_enabled:
            return

        if settings.maintenance_auto_sync_on_startup and settings.bootstrap_manifest_path.exists():
            await self._safe_sync_manifest()

        self._tasks.append(asyncio.create_task(self._cleanup_loop(), name="maintenance-cleanup"))
        if settings.bootstrap_manifest_path.exists():
            self._tasks.append(asyncio.create_task(self._sync_loop(), name="maintenance-sync"))
        else:
            logger.warning(
                "Maintenance manifest sync loop disabled because manifest is missing.",
                extra={"extra_payload": {"manifest_path": str(settings.bootstrap_manifest_path)}},
            )

    async def stop(self) -> None:
        if not self._tasks:
            return
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def _cleanup_loop(self) -> None:
        while True:
            await asyncio.sleep(settings.maintenance_cleanup_interval_seconds)
            try:
                await asyncio.to_thread(
                    self.maintenance_service.cleanup_expired_uploads,
                    catalog=self.catalog,
                    limit=settings.maintenance_cleanup_batch_size,
                )
            except asyncio.CancelledError:  # pragma: no cover
                raise
            except Exception as exc:  # pragma: no cover
                logger.warning(
                    "Scheduled upload cleanup failed.",
                    extra={"extra_payload": {"error": str(exc)}},
                )

    async def _sync_loop(self) -> None:
        while True:
            await asyncio.sleep(settings.maintenance_sync_interval_seconds)
            await self._safe_sync_manifest()

    async def _safe_sync_manifest(self) -> None:
        try:
            await asyncio.to_thread(
                self.maintenance_service.sync_manifest,
                catalog=self.catalog,
                manifest_path=settings.bootstrap_manifest_path,
                persist=True,
            )
        except FileNotFoundError:
            logger.warning(
                "Scheduled manifest sync skipped because manifest is missing.",
                extra={"extra_payload": {"manifest_path": str(settings.bootstrap_manifest_path)}},
            )
        except asyncio.CancelledError:  # pragma: no cover
            raise
        except Exception as exc:  # pragma: no cover
            logger.warning(
                "Scheduled manifest sync failed.",
                extra={"extra_payload": {"error": str(exc), "manifest_path": str(settings.bootstrap_manifest_path)}},
            )

