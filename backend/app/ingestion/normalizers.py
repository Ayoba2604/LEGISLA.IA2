from __future__ import annotations

import hashlib
import re

from backend.app.core.text import normalize_text


def normalize_document_text(text: str) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return normalize_text(cleaned)


def compute_document_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

