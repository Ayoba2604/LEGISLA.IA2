from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.enums import ResponseMode, SourceAuthority, SourceType
from backend.app.core.text import stable_id
from backend.app.ingestion.chunkers import chunk_source
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.models.domain import SourceMetadata, SourceRecord
from backend.app.schemas.chat import ChatRequest
from backend.app.security.tokens import AuthenticatedUser
from backend.app.services.chat_service import ChatService
from backend.app.services.source_catalog import SourceCatalog

DATASET_PATH = ROOT / "backend" / "data" / "evaluation" / "legal_eval_dataset.json"


def main() -> None:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    default_catalog = build_default_catalog()
    user_catalog, user_source_id = build_user_document_catalog()
    empty_catalog = SourceCatalog()
    pipeline = IngestionPipeline()
    authenticated_user = AuthenticatedUser(
        user_id="user-42",
        email="usuario@legisla.ai",
        admin=False,
        session_id="sessao-eval",
        issued_at=100,
        expires_at=10_000,
    )

    total_checks = 0
    matched_checks = 0
    rows = []

    for item in dataset:
        if item["kind"] == "chat":
            if item["profile"] == "default":
                service = ChatService(default_catalog)
                user = None
                user_document_ids = []
            elif item["profile"] == "user_document":
                service = ChatService(user_catalog)
                user = authenticated_user
                user_document_ids = [user_source_id]
            else:
                service = ChatService(empty_catalog)
                user = None
                user_document_ids = []

            response = service.answer(
                ChatRequest(
                    question=item["question"],
                    mode=ResponseMode(item["mode"]),
                    user_document_ids=user_document_ids,
                ),
                authenticated_user=user,
            )
            observation = {
                "sufficient_support": response.sufficient_support,
                "has_citations": bool(response.fontes_consultadas),
                "intent": response.intent,
                "source_type": response.fontes_consultadas[0].source_type.value if response.fontes_consultadas else None,
                "confidence_level": response.confidence_level,
                "requires_human_escalation": response.requires_human_escalation,
                "limites_texto": " ".join(response.limites).lower(),
                "resposta_texto": response.resposta_objetiva.lower(),
                "fontes_titulos": [citation.title.lower() for citation in response.fontes_consultadas],
                "fontes_tipos": [citation.source_type.value for citation in response.fontes_consultadas],
            }
        else:
            _, _, _, injection_detected = pipeline.ingest_upload(
                filename=item["filename"],
                mime_type=item["mime_type"],
                payload=item["payload"].encode("utf-8"),
            )
            observation = {"prompt_injection": injection_detected}

        checks = item["checks"]
        result = {"id": item["id"], "observation": observation, "checks": {}}
        for key, expected in checks.items():
            matched, observed = evaluate_check(key, expected, observation)
            result["checks"][key] = {"expected": expected, "observed": observed, "matched": matched}
            total_checks += 1
            matched_checks += int(matched)
        rows.append(result)

    report = {
        "total_cases": len(dataset),
        "total_checks": total_checks,
        "matched_checks": matched_checks,
        "match_rate": round(matched_checks / total_checks, 4) if total_checks else 0.0,
        "rows": rows,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


def build_default_catalog() -> SourceCatalog:
    catalog = SourceCatalog()
    add_text_source(
        catalog,
        title="Codigo de Defesa do Consumidor",
        source_type=SourceType.LEGISLATION,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        text=(
            "Lei 8.078/1990. Art. 6. Sao direitos basicos do consumidor a protecao da vida, saude e seguranca. "
            "Art. 49. O consumidor pode desistir do contrato, no prazo de 7 dias, quando a contratacao ocorrer fora do estabelecimento comercial."
        ),
        metadata=SourceMetadata(numero_norma="Lei 8.078/1990", artigo="6", vigencia="vigente", tema="Direito do consumidor"),
    )
    add_text_source(
        catalog,
        title="Lei Municipal 123/1990",
        source_type=SourceType.LEGISLATION,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        text=(
            "Lei Municipal 123/1990.\n"
            "Art. 1. Norma historica sobre ocupacao urbana municipal.\n"
            "Vigencia: revogada pela Lei Municipal 456/2005."
        ),
        metadata=SourceMetadata(numero_norma="Lei Municipal 123/1990", vigencia="revogada", tema="Vigencia normativa"),
    )
    add_text_source(
        catalog,
        title="STJ - atraso de voo com dano moral presumido",
        source_type=SourceType.JURISPRUDENCE,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        text=(
            "EMENTA. Atraso de voo superior a quatro horas. Dano moral reconhecido em razao da falha grave na prestacao do servico. "
            "Tese: o atraso qualificado pode gerar dano moral indenizavel."
        ),
        metadata=SourceMetadata(
            tribunal="STJ",
            numero_processo="REsp 1111111",
            relator="Ministro Exemplo A",
            tema="Transporte aereo",
        ),
    )
    add_text_source(
        catalog,
        title="TJSP - atraso de voo sem dano moral automatico",
        source_type=SourceType.JURISPRUDENCE,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        text=(
            "EMENTA. Atraso de voo com reacomodacao adequada. Dano moral nao configurado automaticamente. "
            "Tese: e necessario demonstrar repercussao concreta acima do mero aborrecimento."
        ),
        metadata=SourceMetadata(
            tribunal="TJSP",
            numero_processo="Apelacao 2222222",
            relator="Desembargador Exemplo B",
            tema="Transporte aereo",
        ),
    )
    add_text_source(
        catalog,
        title="Sumula 297 do STJ",
        source_type=SourceType.SUMULA,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        text="Sumula 297 do STJ. O Codigo de Defesa do Consumidor e aplicavel as instituicoes financeiras.",
        metadata=SourceMetadata(
            tribunal="STJ",
            sumula_numero="297",
            numero_norma="Sumula 297",
            enunciado="O Codigo de Defesa do Consumidor e aplicavel as instituicoes financeiras.",
            tema="Instituicoes financeiras e CDC",
        ),
    )
    add_text_source(
        catalog,
        title="Contrato de servico com multa elevada",
        source_type=SourceType.CONTRACT,
        authority=SourceAuthority.SECONDARY,
        is_official=False,
        is_primary=False,
        text=(
            "CLAUSULA 5. Em caso de cancelamento pelo contratante, sera devida multa compensatoria de 50% do valor total. "
            "CLAUSULA 6. Nao havera reembolso em nenhuma hipotese."
        ),
        metadata=SourceMetadata(tema="Analise contratual"),
    )
    return catalog


def build_user_document_catalog() -> tuple[SourceCatalog, str]:
    catalog = build_default_catalog()
    source = SourceRecord(
        source_id=stable_id("user-document", "cdc-conflict"),
        document_id=stable_id("document", "user-document", "cdc-conflict"),
        version_id=stable_id("version", "user-document", "cdc-conflict"),
        title="Documento do usuario sobre reembolso",
        source_type=SourceType.USER_DOCUMENT,
        authority=SourceAuthority.PRIVATE,
        is_official=False,
        is_primary=True,
        description="Documento enviado para avaliacao",
        raw_text=(
            "CLAUSULA 1. O consumidor renuncia integralmente a qualquer reembolso, inclusive em caso de cancelamento em prazo legal."
        ),
        metadata=SourceMetadata(
            tema="Documento privado",
            metadata_extra={"owner_user_id": "user-42", "owner_email": "usuario@legisla.ai"},
        ),
    )
    catalog.add_source(source, chunk_source(source), persist=False)
    return catalog, source.source_id


def add_text_source(
    catalog: SourceCatalog,
    *,
    title: str,
    source_type: SourceType,
    authority: SourceAuthority,
    is_official: bool,
    is_primary: bool,
    text: str,
    metadata: SourceMetadata,
) -> None:
    source = SourceRecord(
        source_id=stable_id(title, source_type.value),
        document_id=stable_id("document", title, source_type.value),
        version_id=stable_id("version", title, text),
        title=title,
        source_type=source_type,
        authority=authority,
        is_official=is_official,
        is_primary=is_primary,
        description=title,
        raw_text=text,
        metadata=metadata,
    )
    catalog.add_source(source, chunk_source(source), persist=False)


def evaluate_check(key: str, expected, observation: dict) -> tuple[bool, object]:
    observed = observation.get(key)
    if key.endswith("_contains"):
        haystack = str(observation.get(key.removesuffix("_contains"), ""))
        return str(expected).lower() in haystack.lower(), haystack
    if key.endswith("_contains_any"):
        haystack = str(observation.get(key.removesuffix("_contains_any"), ""))
        expected_values = [str(item).lower() for item in expected]
        return any(item in haystack.lower() for item in expected_values), haystack
    if key.endswith("_includes"):
        values = observation.get(key.removesuffix("_includes"), []) or []
        expected_value = str(expected).lower()
        normalized = [str(item).lower() for item in values]
        return any(expected_value in item for item in normalized), normalized
    if key.endswith("_includes_any"):
        values = observation.get(key.removesuffix("_includes_any"), []) or []
        normalized = [str(item).lower() for item in values]
        expected_values = [str(item).lower() for item in expected]
        return any(any(expected_value in item for item in normalized) for expected_value in expected_values), normalized
    return observed == expected, observed


if __name__ == "__main__":
    main()
