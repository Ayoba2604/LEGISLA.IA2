from __future__ import annotations

from backend.app.core.text import normalize_text, stable_id
from backend.app.ingestion.legal_metadata import build_chunk_metadata, build_source_segments
from backend.app.models.domain import ChunkRecord, SourceRecord


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
    structured_segments = build_source_segments(source.source_type, source.raw_text, source.hierarchy)

    if structured_segments:
        iterable = [
            (
                segment.content,
                segment.hierarchy,
                build_chunk_metadata(source.metadata, segment),
                segment.title_suffix,
                segment.search_text,
            )
            for segment in structured_segments
        ]
    else:
        iterable = [
            (segment, source.hierarchy, source.metadata, None, None)
            for segment in _semantic_paragraph_chunks(source.raw_text)
        ]

    chunks: list[ChunkRecord] = []
    for index, (segment, hierarchy, metadata, title_suffix, search_text) in enumerate(iterable):
        chunk_id = stable_id(source.source_id, str(index), segment[:200])
        chunk_title = source.title if not title_suffix else f"{source.title} - {title_suffix}"
        chunks.append(
            ChunkRecord(
                chunk_id=chunk_id,
                source_id=source.source_id,
                document_id=source.document_id,
                version_id=source.version_id,
                title=chunk_title,
                content=segment,
                hierarchy=hierarchy,
                source_type=source.source_type,
                authority=source.authority,
                is_official=source.is_official,
                is_primary=source.is_primary,
                metadata=metadata,
                hash=stable_id(chunk_id, segment),
                search_text=search_text or f"{chunk_title} {segment}",
            )
        )
    return chunks
