from __future__ import annotations

import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
import requests

from backend.app.config.settings import settings

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LegislaIA-Ingestion/2.0",
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
}


def fetch_remote_payload(url: str) -> tuple[bytes, str]:
    hostname = urlparse(url).hostname or ""
    prefer_requests = (not settings.ingest_http_verify_ssl) or hostname.endswith("planalto.gov.br")
    last_error: Exception | None = None
    strategies = (_fetch_with_requests, _fetch_with_httpx) if prefer_requests else (_fetch_with_httpx, _fetch_with_requests)
    for strategy in strategies:
        for attempt in range(settings.ingest_http_max_retries + 1):
            try:
                return strategy(url)
            except Exception as exc:  # pragma: no cover
                last_error = exc
                if attempt < settings.ingest_http_max_retries:
                    time.sleep(min(1.5 * (attempt + 1), 3.0))
    raise RuntimeError(f"Failed to fetch remote source: {url}") from last_error


def _fetch_with_httpx(url: str) -> tuple[bytes, str]:
    with httpx.Client(
        follow_redirects=True,
        timeout=settings.ingest_http_timeout_seconds,
        headers=DEFAULT_HEADERS,
        verify=settings.ingest_http_verify_ssl,
    ) as client:
        response = client.get(url)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "application/octet-stream").split(";")[0].strip()
        payload = response.content
        if len(payload) > settings.max_upload_bytes:
            raise ValueError("Remote payload exceeds configured size limit.")
        return payload, content_type


def _fetch_with_requests(url: str) -> tuple[bytes, str]:
    response = requests.get(
        url,
        headers=DEFAULT_HEADERS,
        timeout=settings.ingest_http_timeout_seconds,
        allow_redirects=True,
        verify=settings.ingest_http_verify_ssl,
    )
    response.raise_for_status()
    content_type = response.headers.get("content-type", "application/octet-stream").split(";")[0].strip()
    payload = response.content
    if len(payload) > settings.max_upload_bytes:
        raise ValueError("Remote payload exceeds configured size limit.")
    return payload, content_type


def load_local_payload(path: str) -> tuple[bytes, str]:
    file_path = Path(path)
    payload = file_path.read_bytes()
    if len(payload) > settings.max_upload_bytes:
        raise ValueError(f"Local payload exceeds configured size limit: {file_path}")
    suffix = file_path.suffix.lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".json": "application/json",
        ".html": "text/html",
        ".htm": "text/html",
        ".md": "text/markdown",
        ".txt": "text/plain",
    }
    return payload, mime_map.get(suffix, "application/octet-stream")
