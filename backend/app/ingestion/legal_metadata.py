from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from backend.app.core.enums import SourceType
from backend.app.core.text import normalize_text
from backend.app.models.domain import SourceMetadata

ARTICLE_LINE_RE = re.compile(r"^Art(?:igo)?\.?\s*(\d+[A-Za-z0-9o-]*)", re.IGNORECASE)
PARAGRAPH_RE = re.compile(r"(Par[aá]grafo\s+[uú]nico|§+\s*\d+[ºo]?)", re.IGNORECASE)
HEADING_PATTERNS = {
    "parte": re.compile(r"^PARTE\b.*", re.IGNORECASE),
    "livro": re.compile(r"^LIVRO\b.*", re.IGNORECASE),
    "titulo_normativo": re.compile(r"^T[IÍ]TULO\b.*", re.IGNORECASE),
    "capitulo": re.compile(r"^CAP[IÍ]TULO\b.*", re.IGNORECASE),
    "secao": re.compile(r"^SE[CÇ][AÃ]O\b.*", re.IGNORECASE),
    "subsecao": re.compile(r"^SUBSE[CÇ][AÃ]O\b.*", re.IGNORECASE),
}
JURISPRUDENCE_SECTION_RE = re.compile(
    r"^(EMENTA|RELATORIO|FUNDAMENTOS|VOTO|DECISAO|DISPOSITIVO|TESE JURIDICA|ACORDAO|REFERENCIAS LEGISLATIVAS)\s*:?\s*$",
    re.IGNORECASE,
)
CLAUSE_RE = re.compile(r"^(CL[AÁ]USULA\s+\d+[A-Za-z-]*|[0-9]+(?:\.[0-9]+)*)\b", re.IGNORECASE)
SUMULA_ENTRY_RE = re.compile(r"^(S[UÚ]MULA(?:\s+VINCULANTE)?\s+(?:N[.º°]\s*)?\d+)\b", re.IGNORECASE)
NORM_NUMBER_RE = re.compile(
    r"\b((?:Lei|Decreto-?Lei|Decreto|Medida Provis[oó]ria|Constitui[cç][aã]o)[^\n]{0,80}\d[\d./-]*)",
    re.IGNORECASE,
)
LABELED_VALUE_RE = {
    "tribunal": re.compile(r"^TRIBUNAL:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "orgao_julgador": re.compile(r"^ORGAO JULGADOR:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "numero_processo": re.compile(r"^NUMERO DO PROCESSO:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "relator": re.compile(r"^RELATOR:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "tese_juridica": re.compile(r"TESE JURIDICA:\s*(.+?)(?:\n[A-Z][A-Z\\s]+:|\Z)", re.IGNORECASE | re.DOTALL),
    "dispositivo": re.compile(r"DISPOSITIVO:\s*(.+?)(?:\n[A-Z][A-Z\\s]+:|\Z)", re.IGNORECASE | re.DOTALL),
    "enunciado": re.compile(r"ENUNCIADO:\s*(.+?)(?:\n[A-Z][A-Z\\s]+:|\Z)", re.IGNORECASE | re.DOTALL),
}


@dataclass
class SegmentSpec:
    content: str
    hierarchy: list[str]
    metadata_updates: dict[str, Any] = field(default_factory=dict)
    metadata_extra_updates: dict[str, Any] = field(default_factory=dict)
    title_suffix: str | None = None
    search_text: str | None = None


def enrich_source_metadata(
    *,
    source_type: SourceType,
    title: str,
    text: str,
    metadata: SourceMetadata,
) -> SourceMetadata:
    updates: dict[str, Any] = {}
    if source_type == SourceType.LEGISLATION:
        if not metadata.numero_norma:
            norm_number = _extract_norm_number(text) or _extract_norm_number(title)
            if norm_number:
                updates["numero_norma"] = norm_number
        if not metadata.vigencia:
            lowered = (text or "").lower()
            if "revogad" in lowered:
                updates["vigencia"] = "revogada"
            elif text:
                updates["vigencia"] = "vigente"
    elif source_type in {SourceType.JURISPRUDENCE, SourceType.PROCESS_METADATA}:
        for field_name, pattern in LABELED_VALUE_RE.items():
            if getattr(metadata, field_name, None):
                continue
            match = pattern.search(text or "")
            if match:
                updates[field_name] = normalize_text(match.group(1))
        if not metadata.data_publicacao:
            publication = _extract_labeled_value(text, "DATA DA PUBLICACAO")
            parsed_date = _parse_date(publication)
            if parsed_date:
                updates["data_publicacao"] = parsed_date
        if not metadata.data_julgamento:
            judgment = _extract_labeled_value(text, "DATA DA DECISAO")
            parsed_date = _parse_date(judgment)
            if parsed_date:
                updates["data_julgamento"] = parsed_date
    elif source_type == SourceType.SUMULA:
        if not metadata.sumula_numero:
            match = SUMULA_ENTRY_RE.search(text or title)
            if match:
                updates["sumula_numero"] = _digits_only(match.group(1))
        if not metadata.numero_norma and updates.get("sumula_numero"):
            updates["numero_norma"] = f"Sumula {updates['sumula_numero']}"
        if not metadata.enunciado:
            enunciado = _extract_labeled_value(text, "ENUNCIADO")
            if enunciado:
                updates["enunciado"] = enunciado

    if not updates:
        return metadata
    return metadata.model_copy(update=updates)


def build_source_segments(source_type: SourceType, text: str, base_hierarchy: list[str]) -> list[SegmentSpec]:
    if source_type == SourceType.LEGISLATION:
        return _build_legislation_segments(text, base_hierarchy)
    if source_type == SourceType.JURISPRUDENCE:
        return _build_jurisprudence_segments(text, base_hierarchy)
    if source_type == SourceType.SUMULA:
        return _build_sumula_segments(text, base_hierarchy)
    if source_type in {SourceType.CONTRACT, SourceType.USER_DOCUMENT}:
        return _build_clause_segments(text, base_hierarchy)
    if source_type == SourceType.PROCESS_METADATA:
        return _build_process_segments(text, base_hierarchy)
    return []


def build_chunk_metadata(base_metadata: SourceMetadata, segment: SegmentSpec) -> SourceMetadata:
    metadata_extra = {**base_metadata.metadata_extra, **segment.metadata_extra_updates}
    return base_metadata.model_copy(update={**segment.metadata_updates, "metadata_extra": metadata_extra})


def _clean_lines(text: str) -> list[str]:
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


def _build_legislation_segments(text: str, base_hierarchy: list[str]) -> list[SegmentSpec]:
    prepared_text = re.sub(r"(?<!\n)(?=\bArt(?:igo)?\.?\s*\d+[A-Za-z0-9o-]*)", "\n", text or "")
    prepared_text = re.sub(r"(?<!\n)(?=\b(?:PARTE|LIVRO|T[IÍ]TULO|CAP[IÍ]TULO|SE[CÇ][AÃ]O|SUBSE[CÇ][AÃ]O)\b)", "\n", prepared_text)
    lines = _clean_lines(prepared_text)
    if not lines:
        return []

    context = {
        "parte": None,
        "livro": None,
        "titulo_normativo": None,
        "capitulo": None,
        "secao": None,
        "subsecao": None,
    }
    segments: list[SegmentSpec] = []
    preamble: list[str] = []
    article_lines: list[str] = []
    article_context = context.copy()
    article_label: str | None = None

    def flush_article() -> None:
        if not article_lines:
            return
        content = "\n".join(article_lines).strip()
        hierarchy = [*base_hierarchy]
        for field_name in ("parte", "livro", "titulo_normativo", "capitulo", "secao", "subsecao"):
            value = article_context.get(field_name)
            if value:
                hierarchy.append(value)
        if article_label:
            hierarchy.append(f"art. {article_label}")
        paragraph = PARAGRAPH_RE.search(content)
        metadata_updates = {
            key: value
            for key, value in article_context.items()
            if value is not None
        }
        metadata_updates["artigo"] = article_label
        if paragraph:
            metadata_updates["paragrafo"] = normalize_text(paragraph.group(1))
        segments.append(
            SegmentSpec(
                content=content,
                hierarchy=hierarchy,
                metadata_updates=metadata_updates,
                metadata_extra_updates={
                    "incisos_presentes": re.findall(r"^\s*([IVXLCDM]+)\s*[-–]", content, flags=re.IGNORECASE | re.MULTILINE),
                    "alineas_presentes": re.findall(r"^\s*([a-z])\)", content, flags=re.IGNORECASE | re.MULTILINE),
                },
                title_suffix=f"Art. {article_label}" if article_label else None,
                search_text=f"artigo {article_label or ''} {content}".strip(),
            )
        )

    for line in lines:
        heading_applied = False
        for field_name, pattern in HEADING_PATTERNS.items():
            if pattern.match(line):
                if article_lines:
                    flush_article()
                    article_lines = []
                    article_label = None
                context[field_name] = line
                if field_name == "parte":
                    context.update({"livro": None, "titulo_normativo": None, "capitulo": None, "secao": None, "subsecao": None})
                elif field_name == "livro":
                    context.update({"titulo_normativo": None, "capitulo": None, "secao": None, "subsecao": None})
                elif field_name == "titulo_normativo":
                    context.update({"capitulo": None, "secao": None, "subsecao": None})
                elif field_name == "capitulo":
                    context.update({"secao": None, "subsecao": None})
                elif field_name == "secao":
                    context.update({"subsecao": None})
                heading_applied = True
                break
        if heading_applied:
            continue

        article_match = ARTICLE_LINE_RE.match(line)
        if article_match:
            if article_lines:
                flush_article()
                article_lines = []
            article_label = article_match.group(1)
            article_context = context.copy()
            article_lines = [line]
            continue

        if article_lines:
            article_lines.append(line)
        else:
            preamble.append(line)

    if article_lines:
        flush_article()

    if preamble:
        segments.insert(
            0,
            SegmentSpec(
                content="\n".join(preamble).strip(),
                hierarchy=[*base_hierarchy, "preambulo"],
                metadata_extra_updates={"segment_type": "preambulo"},
                title_suffix="Preambulo",
            )
        )
    return segments


def _build_jurisprudence_segments(text: str, base_hierarchy: list[str]) -> list[SegmentSpec]:
    lines = _clean_lines(text)
    if not lines:
        return []

    segments: list[SegmentSpec] = []
    current_header = "METADADOS"
    current_lines: list[str] = []

    def flush_section() -> None:
        if not current_lines:
            return
        content = "\n".join(current_lines).strip()
        section_label = current_header.lower()
        metadata_updates: dict[str, Any] = {}
        if section_label == "tese juridica":
            metadata_updates["tese_juridica"] = content
        if section_label == "dispositivo":
            metadata_updates["dispositivo"] = content
        if section_label == "ementa":
            metadata_updates["enunciado"] = content
        segments.append(
            SegmentSpec(
                content=content,
                hierarchy=[*base_hierarchy, section_label],
                metadata_updates=metadata_updates,
                metadata_extra_updates={"jurisprudencia_secao": section_label},
                title_suffix=current_header.title(),
                search_text=f"{current_header} {content}",
            )
        )

    for line in lines:
        header_match = JURISPRUDENCE_SECTION_RE.match(line)
        if header_match:
            flush_section()
            current_header = normalize_text(header_match.group(1)).upper()
            current_lines = []
            continue
        current_lines.append(line)

    flush_section()
    return segments


def _build_sumula_segments(text: str, base_hierarchy: list[str]) -> list[SegmentSpec]:
    lines = _clean_lines(text)
    if not lines:
        return []

    segments: list[SegmentSpec] = []
    current_label = None
    current_lines: list[str] = []

    def flush_sumula() -> None:
        if not current_lines:
            return
        content = "\n".join(current_lines).strip()
        sumula_number = _digits_only(current_label or "") or _digits_only(content)
        hierarchy = [*base_hierarchy]
        if sumula_number:
            hierarchy.append(f"sumula {sumula_number}")
        segments.append(
            SegmentSpec(
                content=content,
                hierarchy=hierarchy,
                metadata_updates={
                    "sumula_numero": sumula_number,
                    "numero_norma": f"Sumula {sumula_number}" if sumula_number else None,
                    "enunciado": content,
                },
                metadata_extra_updates={"segment_type": "sumula"},
                title_suffix=current_label.title() if current_label else "Sumula",
                search_text=f"{current_label or 'sumula'} {content}",
            )
        )

    for line in lines:
        entry_match = SUMULA_ENTRY_RE.match(line)
        if entry_match:
            flush_sumula()
            current_label = normalize_text(entry_match.group(1))
            current_lines = [line]
            continue
        current_lines.append(line)

    flush_sumula()
    return segments


def _build_clause_segments(text: str, base_hierarchy: list[str]) -> list[SegmentSpec]:
    lines = _clean_lines(text)
    if not lines:
        return []

    segments: list[SegmentSpec] = []
    current_label = None
    current_lines: list[str] = []

    def flush_clause() -> None:
        if not current_lines:
            return
        content = "\n".join(current_lines).strip()
        clause_id = _normalize_clause_label(current_label)
        hierarchy = [*base_hierarchy]
        if clause_id:
            hierarchy.append(clause_id)
        segments.append(
            SegmentSpec(
                content=content,
                hierarchy=hierarchy,
                metadata_extra_updates={"clausula": clause_id},
                title_suffix=clause_id or "Clausula",
                search_text=f"{clause_id or 'clausula'} {content}",
            )
        )

    for line in lines:
        clause_match = CLAUSE_RE.match(line)
        if clause_match:
            flush_clause()
            current_label = clause_match.group(1)
            current_lines = [line]
            continue
        current_lines.append(line)

    flush_clause()
    return segments


def _build_process_segments(text: str, base_hierarchy: list[str]) -> list[SegmentSpec]:
    lines = _clean_lines(text)
    if not lines:
        return []
    return [
        SegmentSpec(
            content="\n".join(lines).strip(),
            hierarchy=[*base_hierarchy, "metadados-processuais"],
            metadata_extra_updates={"segment_type": "process_metadata"},
            title_suffix="Metadados Processuais",
        )
    ]


def _extract_norm_number(value: str) -> str | None:
    match = NORM_NUMBER_RE.search(value or "")
    return normalize_text(match.group(1)) if match else None


def _extract_labeled_value(text: str, label: str) -> str | None:
    pattern = re.compile(rf"^{re.escape(label)}:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text or "")
    return normalize_text(match.group(1)) if match else None


def _parse_date(raw: str | None):
    if not raw:
        return None
    value = normalize_text(raw)
    for pattern in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, pattern).date()
        except ValueError:
            continue
    compact = re.search(r"(\d{8})", value)
    if compact:
        try:
            return datetime.strptime(compact.group(1), "%Y%m%d").date()
        except ValueError:
            return None
    ddmmyyyy = re.search(r"(\d{2}/\d{2}/\d{4})", value)
    if ddmmyyyy:
        try:
            return datetime.strptime(ddmmyyyy.group(1), "%d/%m/%Y").date()
        except ValueError:
            return None
    return None


def _digits_only(value: str) -> str | None:
    digits = "".join(re.findall(r"\d+", value or ""))
    return digits or None


def _normalize_clause_label(value: str | None) -> str | None:
    if not value:
        return None
    normalized = normalize_text(value)
    normalized = normalized.replace("CLÁUSULA", "Clausula").replace("CLAUSULA", "Clausula")
    return normalized
