from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from backend.app.config.settings import settings
from backend.app.connectors.models import (
    DataJudQuerySpec,
    OfficialCorpusBuildReport,
    OfficialCorpusRegistry,
    PlanaltoLegislationSpec,
    StjOpenDataSpec,
)
from backend.app.core.enums import SourceAuthority, SourceType
from backend.app.core.text import stable_id
from backend.app.ingestion.fetchers import fetch_remote_payload
from backend.app.models.domain import SourceMetadata
from backend.app.schemas.ingestion import ManifestSourceSpec

logger = logging.getLogger(__name__)


class OfficialCorpusBuilder:
    def __init__(self, *, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "LegislaIA-OfficialCorpus/2.0"})

    def build_from_registry_file(
        self,
        registry_path: Path,
        *,
        manifest_output_path: Path | None = None,
        snapshot_root: Path | None = None,
    ) -> OfficialCorpusBuildReport:
        registry = OfficialCorpusRegistry.model_validate(
            json.loads(registry_path.read_text(encoding="utf-8"))
        )
        output_manifest = manifest_output_path or Path(registry.manifest_output_path)
        output_snapshot_root = snapshot_root or Path(registry.snapshot_root)
        output_manifest.parent.mkdir(parents=True, exist_ok=True)
        output_snapshot_root.mkdir(parents=True, exist_ok=True)

        warnings: list[str] = []
        manifest_entries: list[ManifestSourceSpec] = []
        connectors_run: list[str] = []
        failed_sources = 0

        for spec in registry.planalto_legislation:
            if not spec.enabled:
                continue
            connectors_run.append("planalto_legislation")
            try:
                manifest_entries.append(self._collect_planalto_legislation(spec, output_snapshot_root))
            except Exception as exc:
                failed_sources += 1
                warnings.append(f"{spec.title}: falha na coleta Planalto ({exc})")

        for spec in registry.stj_open_data:
            if not spec.enabled:
                continue
            connectors_run.append("stj_open_data")
            try:
                manifest_entries.extend(self._collect_stj_open_data(spec, output_snapshot_root))
            except Exception as exc:
                failed_sources += 1
                warnings.append(f"{spec.package_name}: falha na coleta STJ ({exc})")

        for spec in registry.datajud_queries:
            if not spec.enabled:
                continue
            connectors_run.append("datajud_query")
            try:
                manifest_entries.extend(self._collect_datajud_query(spec, output_snapshot_root))
            except Exception as exc:
                failed_sources += 1
                warnings.append(f"{spec.name}: falha na coleta DataJud ({exc})")

        output_manifest.write_text(
            json.dumps(
                [entry.model_dump(mode="json", exclude_none=True) for entry in manifest_entries],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return OfficialCorpusBuildReport(
            registry_path=str(registry_path),
            manifest_path=str(output_manifest),
            snapshot_root=str(output_snapshot_root),
            connectors_run=sorted(set(connectors_run)),
            collected_sources=len(manifest_entries),
            failed_sources=failed_sources,
            warnings=warnings,
        )

    def _collect_planalto_legislation(
        self,
        spec: PlanaltoLegislationSpec,
        snapshot_root: Path,
    ) -> ManifestSourceSpec:
        payload, _ = fetch_remote_payload(spec.url)
        filename = f"{_safe_slug(spec.numero_norma)}.html"
        target = snapshot_root / "planalto" / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        return ManifestSourceSpec(
            title=spec.title,
            source_type=SourceType.LEGISLATION,
            authority=SourceAuthority.PRIMARY,
            description=f"Fonte primaria oficial coletada do Planalto: {spec.numero_norma}",
            path=str(target),
            mime_type="text/html",
            is_official=True,
            is_primary=True,
            hierarchy=["legislacao", *spec.hierarchy],
            metadata=SourceMetadata(
                numero_norma=spec.numero_norma,
                ramo_direito=spec.ramo_direito,
                tema=spec.tema,
                url_origem=spec.url,
                vigencia=spec.vigencia,
                metadata_extra={
                    "tipo_norma": spec.tipo_norma,
                    "collector": "planalto_legislation",
                },
            ),
        )

    def _collect_stj_open_data(
        self,
        spec: StjOpenDataSpec,
        snapshot_root: Path,
    ) -> list[ManifestSourceSpec]:
        package_url = f"https://dadosabertos.web.stj.jus.br/api/3/action/package_show?id={spec.package_name}"
        package_payload = self._request_json("GET", package_url)
        package_data = package_payload["result"]
        resource = self._select_latest_json_resource(package_data.get("resources", []))
        records = self._request_json("GET", resource["url"])
        if not isinstance(records, list):
            raise ValueError("Recurso JSON do STJ nao retornou uma lista de registros.")

        manifest_entries: list[ManifestSourceSpec] = []
        target_dir = snapshot_root / "stj" / spec.package_name
        target_dir.mkdir(parents=True, exist_ok=True)
        selected_records = records[: spec.max_records]
        for record in selected_records:
            if spec.only_with_ementa and not str(record.get("ementa") or "").strip():
                continue
            text = self._render_stj_record(record, resource["url"])
            record_id = record.get("id") or record.get("numeroRegistro") or stable_id(spec.package_name, text[:120])
            filename = f"{_safe_slug(str(record_id))}.txt"
            target = target_dir / filename
            target.write_text(text, encoding="utf-8")
            numero_registro = str(record.get("numeroRegistro") or record.get("numeroProcesso") or "").strip() or None
            manifest_entries.append(
                ManifestSourceSpec(
                    title=self._stj_title(record, spec.title or package_data.get("title") or spec.package_name),
                    source_type=SourceType.JURISPRUDENCE,
                    authority=SourceAuthority.PRIMARY,
                    description=f"Jurisprudencia oficial STJ via dados abertos: {package_data.get('title') or spec.package_name}",
                    path=str(target),
                    mime_type="text/plain",
                    is_official=True,
                    is_primary=True,
                    hierarchy=["jurisprudencia", "stj", spec.package_name],
                    metadata=SourceMetadata(
                        tribunal="STJ",
                        orgao_julgador=record.get("nomeOrgaoJulgador"),
                        numero_processo=numero_registro,
                        relator=record.get("ministroRelator"),
                        data_publicacao=_parse_stj_publication_date(record.get("dataPublicacao")),
                        data_julgamento=_parse_compact_date(record.get("dataDecisao")),
                        ramo_direito=spec.ramo_direito,
                        tema=spec.tema or package_data.get("title"),
                        url_origem=resource["url"],
                        metadata_extra={
                            "collector": "stj_open_data",
                            "stj_dataset": spec.package_name,
                            "stj_record_id": record.get("id"),
                            "sigla_classe": record.get("siglaClasse"),
                            "tipo_decisao": record.get("tipoDeDecisao"),
                            "referencias_legislativas": record.get("referenciasLegislativas") or [],
                        },
                    ),
                )
            )
        return manifest_entries

    def _collect_datajud_query(
        self,
        spec: DataJudQuerySpec,
        snapshot_root: Path,
    ) -> list[ManifestSourceSpec]:
        headers = dict(spec.extra_headers)
        if settings.datajud_api_key and settings.datajud_api_header_name not in headers:
            headers[settings.datajud_api_header_name] = f"{settings.datajud_api_header_prefix}{settings.datajud_api_key}"
        if not headers:
            raise ValueError("Conector DataJud exige credencial oficial configurada.")

        response = self._request_json("POST", spec.endpoint, json_payload=spec.payload, headers=headers)
        hits = ((response.get("hits") or {}).get("hits")) or []
        manifest_entries: list[ManifestSourceSpec] = []
        target_dir = snapshot_root / "datajud" / _safe_slug(spec.name)
        target_dir.mkdir(parents=True, exist_ok=True)

        for hit in hits[: spec.max_records]:
            source = hit.get("_source") or {}
            source_id = source.get("id") or source.get("numeroProcesso") or stable_id(spec.name, json.dumps(source, ensure_ascii=False)[:120])
            text = self._render_datajud_source(source, spec)
            target = target_dir / f"{_safe_slug(str(source_id))}.txt"
            target.write_text(text, encoding="utf-8")
            manifest_entries.append(
                ManifestSourceSpec(
                    title=f"{spec.tribunal or 'DataJud'} - {source.get('numeroProcesso') or source.get('classe') or source_id}",
                    source_type=SourceType.PROCESS_METADATA,
                    authority=SourceAuthority.PRIMARY,
                    description=f"Metadados processuais publicos via DataJud: {spec.name}",
                    path=str(target),
                    mime_type="text/plain",
                    is_official=True,
                    is_primary=True,
                    hierarchy=["processos", "datajud", _safe_slug(spec.name)],
                    metadata=SourceMetadata(
                        tribunal=spec.tribunal or source.get("tribunal"),
                        numero_processo=source.get("numeroProcesso"),
                        uf=source.get("uf"),
                        ramo_direito=spec.ramo_direito,
                        tema=spec.tema or spec.name,
                        url_origem=spec.endpoint,
                        metadata_extra={
                            "collector": "datajud_query",
                            "datajud_query": spec.name,
                        },
                    ),
                )
            )
        return manifest_entries

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        json_payload: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        response = self.session.request(
            method=method,
            url=url,
            json=json_payload,
            headers=headers,
            timeout=settings.ingest_http_timeout_seconds,
            verify=settings.ingest_http_verify_ssl,
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _select_latest_json_resource(resources: list[dict[str, Any]]) -> dict[str, Any]:
        json_resources = [item for item in resources if str(item.get("format") or "").upper() == "JSON"]
        if not json_resources:
            raise ValueError("Dataset STJ nao possui recurso JSON.")
        json_resources.sort(key=_resource_sort_key)
        return json_resources[-1]

    @staticmethod
    def _stj_title(record: dict[str, Any], fallback: str) -> str:
        classe = str(record.get("siglaClasse") or fallback).strip()
        numero = str(record.get("numeroRegistro") or record.get("numeroProcesso") or "").strip()
        return f"STJ - {classe} {numero}".strip()

    @staticmethod
    def _render_stj_record(record: dict[str, Any], resource_url: str) -> str:
        sections = [
            "TRIBUNAL: Superior Tribunal de Justica",
            f"ORGAO JULGADOR: {record.get('nomeOrgaoJulgador') or 'Nao informado'}",
            f"CLASSE: {record.get('descricaoClasse') or record.get('siglaClasse') or 'Nao informada'}",
            f"NUMERO DE REGISTRO: {record.get('numeroRegistro') or 'Nao informado'}",
            f"NUMERO DO PROCESSO: {record.get('numeroProcesso') or 'Nao informado'}",
            f"RELATOR: {record.get('ministroRelator') or 'Nao informado'}",
            f"DATA DA DECISAO: {record.get('dataDecisao') or 'Nao informada'}",
            f"DATA DA PUBLICACAO: {record.get('dataPublicacao') or 'Nao informada'}",
            "EMENTA:",
            str(record.get("ementa") or "Nao informada.").strip(),
            "DECISAO:",
            str(record.get("decisao") or "Nao informada.").strip(),
        ]
        if record.get("teseJuridica"):
            sections.extend(["TESE JURIDICA:", str(record.get("teseJuridica")).strip()])
        referencias = record.get("referenciasLegislativas") or []
        if referencias:
            sections.append("REFERENCIAS LEGISLATIVAS:")
            sections.extend(str(item).strip() for item in referencias if str(item).strip())
        sections.extend(
            [
                f"TIPO DE DECISAO: {record.get('tipoDeDecisao') or 'Nao informado'}",
                f"URL DE ORIGEM: {resource_url}",
            ]
        )
        return "\n\n".join(part for part in sections if part)

    @staticmethod
    def _render_datajud_source(source: dict[str, Any], spec: DataJudQuerySpec) -> str:
        sections = [
            f"TRIBUNAL: {spec.tribunal or source.get('tribunal') or 'Nao informado'}",
            f"NUMERO DO PROCESSO: {source.get('numeroProcesso') or 'Nao informado'}",
            f"CLASSE: {source.get('classe') or source.get('classeProcessual') or 'Nao informada'}",
            f"ASSUNTO: {source.get('assunto') or source.get('assuntos') or 'Nao informado'}",
            f"GRAU: {source.get('grau') or 'Nao informado'}",
            f"DATA DE AJUIZAMENTO: {source.get('dataAjuizamento') or 'Nao informada'}",
            f"ULTIMA ATUALIZACAO: {source.get('dataHoraUltimaAtualizacao') or 'Nao informada'}",
            "JSON PROCESSUAL:",
            json.dumps(source, ensure_ascii=False),
        ]
        return "\n\n".join(str(part).strip() for part in sections if str(part).strip())


def _safe_slug(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-{2,}", "-", lowered)
    return lowered.strip("-") or "item"


def _resource_sort_key(resource: dict[str, Any]) -> tuple[str, str]:
    primary = str(resource.get("last_modified") or resource.get("created") or "")
    secondary = str(resource.get("name") or "")
    return primary, secondary


def _parse_compact_date(raw: Any):
    if not raw:
        return None
    value = str(raw).strip()
    if len(value) != 8 or not value.isdigit():
        return None
    try:
        return datetime.strptime(value, "%Y%m%d").date()
    except ValueError:
        return None


def _parse_stj_publication_date(raw: Any):
    if not raw:
        return None
    match = re.search(r"(\d{2}/\d{2}/\d{4})", str(raw))
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%d/%m/%Y").date()
    except ValueError:
        return None

