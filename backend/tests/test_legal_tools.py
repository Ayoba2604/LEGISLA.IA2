from backend.app.core.enums import SourceAuthority, SourceType
from backend.app.core.text import stable_id
from backend.app.models.domain import Citation, ChunkRecord, RetrievedChunk, SourceMetadata
from backend.app.services.retrieval_service import RetrievalService
from backend.app.services.source_catalog import SourceCatalog
from backend.app.tools.legal_tools import LegalTools


def test_validar_citacoes_detecta_referencia_artigo_falsa():
    catalog = SourceCatalog()
    retrieval_service = RetrievalService(catalog)
    tools = LegalTools(retrieval_service=retrieval_service, catalog=catalog)

    metadata = SourceMetadata(numero_norma="CLT", artigo="473")
    chunk = ChunkRecord(
        chunk_id=stable_id("clt", "473"),
        source_id="source-clt-473",
        document_id="doc-clt-473",
        version_id="ver-clt-473",
        title="Consolidacao das Leis do Trabalho",
        content="Art. 473. O empregado podera deixar de comparecer ao servico sem prejuizo do salario em hipoteses legais.",
        hierarchy=["art. 473"],
        source_type=SourceType.LEGISLATION,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        metadata=metadata,
        hash=stable_id("chunk", "clt", "473"),
        search_text="CLT art. 473 empregado deixar de comparecer ao servico",
    )
    result = RetrievedChunk(
        chunk=chunk,
        vector_score=0.8,
        lexical_score=0.7,
        rerank_score=0.6,
        final_score=0.82,
        reason="artigo exato",
    )

    invalid_citation = Citation(
        citation_id="fake-citation",
        chunk_id=chunk.chunk_id,
        source_id=chunk.source_id,
        title=chunk.title,
        source_type=SourceType.JURISPRUDENCE,
        authority=SourceAuthority.PRIMARY,
        quote="Art. 999. Norma inexistente no contexto recuperado.",
        reference_label="Consolidacao das Leis do Trabalho | art. 999",
        metadata={},
    )

    validation, _ = tools.validar_citacoes([result], citations=[invalid_citation])

    assert validation["validas"] == 0
    assert validation["invalidas"] == 1
    assert any("artigo em referencia divergente" in issue for issue in validation["issues"])
    assert any("source_type divergente" in issue for issue in validation["issues"])
