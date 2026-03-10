from __future__ import annotations

import re

from backend.app.core.enums import SourceType
from backend.app.core.text import normalize_text, stable_id
from backend.app.models.domain import ChunkRecord, SourceRecord

ARTICLE_SPLIT_RE = re.compile(r"(?=\bArt(?:igo)?\.?\s*\d+[A-Za-zº°-]*)", re.IGNORECASE)
SECTION_SPLIT_RE = re.compile(r"(?=^\s*(?:CAP[IÍ]TULO|SE[CÇ][AÃ]O|T[IÍ]TULO)\b)", re.IGNORECASE | re.MULTILINE)
CLAUSE_SPLIT_RE = re.compile(r"(?=^\s*(?:CL[AÁ]USULA|cl[áa]usula|[0-9]+\.)\b)", re.IGNORECASE | re.MULTILINE)
JURISPRUDENCE_SPLIT_RE = re.compile(r"(?=^\s*(?:EMENTA|RELATÓRIO|VOTO|ACÓRDÃO|DISPOSITIVO)\b)", re.IGNORECASE | re.MULTILINE)


def _chunk_by_pattern(text: str, pattern: re.Pattern[str]) -> list[str]:
    parts = [normalize_text(item) for item in pattern.split(text) if normalize_text(item)]
    return parts if parts else [normalize_text(text)]


def _semantic_paragraph_chunks(text: str, max_size: int = 900) -> list[str]:
    paragraphs = [normalize_text(item) for item in text.split("\n\n") if normalize_text(item)]
    if not paragraphs:
        return [normalize_text(text)]

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = paragraph
    if current:
        chunks.append(current)
    return chunks


def chunk_source(source: SourceRecord) -> list[ChunkRecord]:
    if source.source_type == SourceType.LEGISLATION:
        segments = _chunk_by_pattern(source.raw_text, ARTICLE_SPLIT_RE)
        if len(segments) == 1:
            segments = _chunk_by_pattern(source.raw_text, SECTION_SPLIT_RE)
    elif source.source_type == SourceType.JURISPRUDENCE:
        segments = _chunk_by_pattern(source.raw_text, JURISPRUDENCE_SPLIT_RE)
    elif source.source_type in {SourceType.CONTRACT, SourceType.USER_DOCUMENT}:
        segments = _chunk_by_pattern(source.raw_text, CLAUSE_SPLIT_RE)
    else:
        segments = _semantic_paragraph_chunks(source.raw_text)

    chunks: list[ChunkRecord] = []
    for index, segment in enumerate(segments):
        chunk_id = stable_id(source.source_id, str(index), segment[:200])
        chunks.append(
            ChunkRecord(
                chunk_id=chunk_id,
                source_id=source.source_id,
                document_id=source.document_id,
                version_id=source.version_id,
                title=source.title,
                content=segment,
                hierarchy=source.hierarchy,
                source_type=source.source_type,
                authority=source.authority,
                is_official=source.is_official,
                is_primary=source.is_primary,
                metadata=source.metadata,
                hash=stable_id(chunk_id, segment),
                search_text=f"{source.title} {segment}",
            )
        )
    return chunks

