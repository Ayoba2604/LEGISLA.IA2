from __future__ import annotations

import hashlib
import re


def normalize_document_text(text: str) -> str:
    cleaned = (text or "").replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n[ \t]+", "\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    lines = [line.strip() for line in cleaned.split("\n")]
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def compute_document_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()
