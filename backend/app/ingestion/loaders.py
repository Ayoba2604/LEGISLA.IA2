from __future__ import annotations

import io
import json
import re
from html import unescape
from pathlib import Path

try:
    import fitz  # type: ignore
except Exception:  # pragma: no cover
    fitz = None

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:  # pragma: no cover
    BeautifulSoup = None

try:
    from docx import Document  # type: ignore
except Exception:  # pragma: no cover
    Document = None

from backend.app.ingestion.normalizers import normalize_document_text


def load_bytes_as_text(filename: str, mime_type: str, payload: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    mime_type = (mime_type or "").lower()

    if mime_type == "application/pdf" or suffix == ".pdf":
        return _load_pdf(payload)
    if (
        mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or suffix == ".docx"
    ):
        return _load_docx(payload)
    if mime_type == "application/json" or suffix == ".json":
        return _load_json(payload)
    if mime_type in {"text/html", "application/xhtml+xml"} or suffix in {".html", ".htm"}:
        return _load_html(payload)

    return normalize_document_text(payload.decode("utf-8", errors="ignore"))


def _load_pdf(payload: bytes) -> str:
    if fitz is None:
        return ""
    document = fitz.open(stream=io.BytesIO(payload), filetype="pdf")
    text = "\n".join(page.get_text("text") for page in document)
    document.close()
    return normalize_document_text(text)


def _load_docx(payload: bytes) -> str:
    if Document is None:
        return ""
    document = Document(io.BytesIO(payload))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    return normalize_document_text(text)


def _load_json(payload: bytes) -> str:
    data = json.loads(payload.decode("utf-8", errors="ignore"))
    if isinstance(data, list):
        return normalize_document_text("\n".join(json.dumps(item, ensure_ascii=False) for item in data))
    return normalize_document_text(json.dumps(data, ensure_ascii=False))


def _load_html(payload: bytes) -> str:
    raw = payload.decode("utf-8", errors="ignore")
    if BeautifulSoup is not None:
        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return normalize_document_text(soup.get_text("\n", strip=True))

    cleaned = re.sub(r"(?is)<(script|style).*?>.*?</\\1>", " ", raw)
    cleaned = re.sub(r"(?s)<[^>]+>", " ", cleaned)
    cleaned = unescape(cleaned)
    return normalize_document_text(cleaned)
