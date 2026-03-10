from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections import Counter
from typing import Iterable

TOKEN_RE = re.compile(r"[A-Za-z0-9]+", re.UNICODE)
ARTICLE_RE = re.compile(r"\bart(?:igo)?\.?\s*(\d+[A-Za-z0-9o-]*)", re.IGNORECASE)
ARTICLE_NUMBER_RE = re.compile(r"\d+")


def normalize_text(value: str) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def fold_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower()


def tokenize(value: str) -> list[str]:
    return [token for token in TOKEN_RE.findall(fold_text(value)) if len(token) > 1]


def hashed_embedding(value: str, dimensions: int = 256) -> list[float]:
    tokens = tokenize(value)
    if not tokens:
        return [0.0] * dimensions

    vector = [0.0] * dimensions
    for token in tokens:
        bucket = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16) % dimensions
        vector[bucket] += 1.0

    norm = math.sqrt(sum(item * item for item in vector)) or 1.0
    return [item / norm for item in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return float(sum(a * b for a, b in zip(left, right)))


def jaccard_similarity(left: Iterable[str], right: Iterable[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def lexical_overlap_score(query: str, text: str) -> float:
    query_tokens = tokenize(query)
    text_tokens = tokenize(text)
    if not query_tokens or not text_tokens:
        return 0.0

    query_counter = Counter(query_tokens)
    text_counter = Counter(text_tokens)
    matched = 0.0
    for token, count in query_counter.items():
        matched += min(count, text_counter.get(token, 0))
    return matched / max(len(query_tokens), 1)


def extract_article_reference(query: str) -> str | None:
    match = ARTICLE_RE.search(fold_text(query or ""))
    return match.group(1) if match else None


def extract_article_number(query: str) -> str | None:
    reference = extract_article_reference(query or "")
    if not reference:
        return None
    match = ARTICLE_NUMBER_RE.search(reference)
    return match.group(0) if match else None


def contains_article_reference(text: str, article_number: str | None) -> bool:
    if not text or not article_number:
        return False
    normalized = fold_text(text)
    pattern = rf"\bart(?:igo)?\.?\s*{re.escape(article_number)}([^0-9]|$)"
    return re.search(pattern, normalized) is not None


def stable_id(*parts: str) -> str:
    base = "::".join(str(part) for part in parts if part is not None)
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:24]

