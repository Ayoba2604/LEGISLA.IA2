from backend.app.core.enums import SourceAuthority, SourceType
from backend.app.core.text import stable_id
from backend.app.models.domain import ChunkRecord, SourceMetadata, SourceRecord
from backend.app.schemas.retrieval import RetrievalFilters
from backend.app.services.retrieval_service import RetrievalService
from backend.app.services.source_catalog import SourceCatalog


def test_hybrid_retrieval_returns_results():
    catalog = SourceCatalog()
    catalog.load_bootstrap_sources()
    service = RetrievalService(catalog)

    results = service.search("compra com defeito", top_k=3, filters=RetrievalFilters())

    assert results
    assert results[0].chunk.title
    assert results[0].final_score >= 0


def test_article_lookup_prefers_matching_law_context():
    catalog = SourceCatalog()

    constitution_source = SourceRecord(
        source_id="source-cf88",
        document_id="doc-cf88",
        version_id="ver-cf88",
        title="Constituicao da Republica Federativa do Brasil de 1988",
        source_type=SourceType.LEGISLATION,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        raw_text="Art. 14. A soberania popular sera exercida pelo sufragio universal e pelo voto direto e secreto.",
        metadata=SourceMetadata(numero_norma="CF/88", artigo="14"),
    )
    constitution_chunk = ChunkRecord(
        chunk_id=stable_id("cf88", "art14"),
        source_id=constitution_source.source_id,
        document_id=constitution_source.document_id,
        version_id=constitution_source.version_id,
        title=constitution_source.title,
        content="Art. 14. A soberania popular sera exercida pelo sufragio universal e pelo voto direto e secreto.",
        hierarchy=["titulo-ii", "capitulo-iv", "art. 14"],
        source_type=SourceType.LEGISLATION,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        metadata=constitution_source.metadata,
        hash=stable_id("cf88", "art14", "chunk"),
        search_text="Constituicao Federal Art. 14 soberania popular sufragio voto direto secreto",
    )

    cdc_source = SourceRecord(
        source_id="source-cdc",
        document_id="doc-cdc",
        version_id="ver-cdc",
        title="Codigo de Defesa do Consumidor",
        source_type=SourceType.LEGISLATION,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        raw_text="Art. 14. O fornecedor responde pelos danos causados por defeitos na prestacao do servico.",
        metadata=SourceMetadata(numero_norma="Lei 8.078/1990", artigo="14"),
    )
    cdc_chunk = ChunkRecord(
        chunk_id=stable_id("cdc", "art14"),
        source_id=cdc_source.source_id,
        document_id=cdc_source.document_id,
        version_id=cdc_source.version_id,
        title=cdc_source.title,
        content="Art. 14. O fornecedor responde pelos danos causados por defeitos relativos a prestacao do servico.",
        hierarchy=["titulo-i", "capitulo-iv", "art. 14"],
        source_type=SourceType.LEGISLATION,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        metadata=cdc_source.metadata,
        hash=stable_id("cdc", "art14", "chunk"),
        search_text="Codigo de Defesa do Consumidor Art. 14 fornecedor responsabilidade danos defeitos servico",
    )

    catalog.sources[constitution_source.source_id] = constitution_source
    catalog.sources[cdc_source.source_id] = cdc_source
    catalog.chunks[constitution_chunk.chunk_id] = constitution_chunk
    catalog.chunks[cdc_chunk.chunk_id] = cdc_chunk

    service = RetrievalService(catalog)
    results = service.search(
        "Qual e a regra do art. 14 do Codigo de Defesa do Consumidor sobre responsabilidade do fornecedor?",
        top_k=2,
        filters=RetrievalFilters(source_types=["legislation"], only_official=True),
    )

    assert results
    assert results[0].chunk.title == "Codigo de Defesa do Consumidor"
    assert "fornecedor" in results[0].chunk.content.lower()


def test_article_lookup_prefers_sigla_da_norma():
    catalog = SourceCatalog()

    constitution_source = SourceRecord(
        source_id="source-cf129",
        document_id="doc-cf129",
        version_id="ver-cf129",
        title="Constituicao da Republica Federativa do Brasil de 1988",
        source_type=SourceType.LEGISLATION,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        raw_text="Art. 129. Sao funcoes institucionais do Ministerio Publico.",
        metadata=SourceMetadata(numero_norma="CF/88", artigo="129"),
    )
    constitution_chunk = ChunkRecord(
        chunk_id=stable_id("cf88", "art129"),
        source_id=constitution_source.source_id,
        document_id=constitution_source.document_id,
        version_id=constitution_source.version_id,
        title=constitution_source.title,
        content="Art. 129. Sao funcoes institucionais do Ministerio Publico.",
        hierarchy=["titulo-iv", "capitulo-iv", "art. 129"],
        source_type=SourceType.LEGISLATION,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        metadata=constitution_source.metadata,
        hash=stable_id("cf88", "art129", "chunk"),
        search_text="Constituicao Federal Art. 129 funcoes institucionais ministerio publico",
    )

    clt_source = SourceRecord(
        source_id="source-clt",
        document_id="doc-clt",
        version_id="ver-clt",
        title="Consolidacao das Leis do Trabalho",
        source_type=SourceType.LEGISLATION,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        raw_text="Art. 129. Todo empregado tera direito anualmente ao gozo de um periodo de ferias.",
        metadata=SourceMetadata(numero_norma="Decreto-Lei 5.452/1943", artigo="129"),
    )
    clt_chunk = ChunkRecord(
        chunk_id=stable_id("clt", "art129"),
        source_id=clt_source.source_id,
        document_id=clt_source.document_id,
        version_id=clt_source.version_id,
        title=clt_source.title,
        content="Art. 129. Todo empregado tera direito anualmente ao gozo de um periodo de ferias, sem prejuizo da remuneracao.",
        hierarchy=["titulo-ii", "capitulo-iv", "art. 129"],
        source_type=SourceType.LEGISLATION,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        metadata=clt_source.metadata,
        hash=stable_id("clt", "art129", "chunk"),
        search_text="Consolidacao das Leis do Trabalho CLT Art. 129 ferias anuais remuneracao empregado",
    )

    catalog.sources[constitution_source.source_id] = constitution_source
    catalog.sources[clt_source.source_id] = clt_source
    catalog.chunks[constitution_chunk.chunk_id] = constitution_chunk
    catalog.chunks[clt_chunk.chunk_id] = clt_chunk

    service = RetrievalService(catalog)
    results = service.search(
        "O que a CLT preve no art. 129 sobre ferias anuais?",
        top_k=2,
        filters=RetrievalFilters(source_types=["legislation"], only_official=True),
    )

    assert results
    assert results[0].chunk.title == "Consolidacao das Leis do Trabalho"
    assert "ferias" in results[0].chunk.content.lower()


def test_article_lookup_disambiguates_codigo_civil_vs_cpc():
    catalog = SourceCatalog()

    civil_source = SourceRecord(
        source_id="source-cc186",
        document_id="doc-cc186",
        version_id="ver-cc186",
        title="Codigo Civil",
        source_type=SourceType.LEGISLATION,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        raw_text="Art. 186. Aquele que, por acao ou omissao voluntaria, negligencia ou imprudencia, violar direito e causar dano a outrem, ainda que exclusivamente moral, comete ato ilicito.",
        metadata=SourceMetadata(numero_norma="Lei 10.406/2002", artigo="186"),
    )
    civil_chunk = ChunkRecord(
        chunk_id=stable_id("cc", "art186"),
        source_id=civil_source.source_id,
        document_id=civil_source.document_id,
        version_id=civil_source.version_id,
        title=civil_source.title,
        content="Art. 186. Aquele que, por acao ou omissao voluntaria, negligencia ou imprudencia, violar direito e causar dano a outrem, ainda que exclusivamente moral, comete ato ilicito.",
        hierarchy=["parte-geral", "livro-iii", "art. 186"],
        source_type=SourceType.LEGISLATION,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        metadata=civil_source.metadata,
        hash=stable_id("cc", "art186", "chunk"),
        search_text="Codigo Civil Lei 10.406/2002 Art. 186 ato ilicito dano negligencia imprudencia",
    )

    cpc_source = SourceRecord(
        source_id="source-cpc186",
        document_id="doc-cpc186",
        version_id="ver-cpc186",
        title="Codigo de Processo Civil",
        source_type=SourceType.LEGISLATION,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        raw_text="Art. 186. O juiz dirigira o processo conforme as disposicoes deste Codigo.",
        metadata=SourceMetadata(numero_norma="Lei 13.105/2015", artigo="186"),
    )
    cpc_chunk = ChunkRecord(
        chunk_id=stable_id("cpc", "art186"),
        source_id=cpc_source.source_id,
        document_id=cpc_source.document_id,
        version_id=cpc_source.version_id,
        title=cpc_source.title,
        content="Art. 186. O juiz dirigira o processo conforme as disposicoes deste Codigo.",
        hierarchy=["parte-geral", "livro-iv", "art. 186"],
        source_type=SourceType.LEGISLATION,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        metadata=cpc_source.metadata,
        hash=stable_id("cpc", "art186", "chunk"),
        search_text="Codigo de Processo Civil Lei 13.105/2015 Art. 186 juiz dirigira o processo",
    )

    catalog.sources[civil_source.source_id] = civil_source
    catalog.sources[cpc_source.source_id] = cpc_source
    catalog.chunks[civil_chunk.chunk_id] = civil_chunk
    catalog.chunks[cpc_chunk.chunk_id] = cpc_chunk

    service = RetrievalService(catalog)
    results = service.search(
        "O art. 186 do Codigo Civil define ato ilicito?",
        top_k=2,
        filters=RetrievalFilters(source_types=["legislation"], only_official=True),
    )

    assert results
    assert results[0].chunk.title == "Codigo Civil"
    assert "ato ilicito" in results[0].chunk.content.lower()


class StubEmbeddingService:
    model_name = "stub-semantic"

    @staticmethod
    def embed_documents(texts: list[str]) -> list[list[float]]:
        return [StubEmbeddingService.embed_query(text) for text in texts]

    @staticmethod
    def embed_query(text: str) -> list[float]:
        lowered = text.lower()
        if "assassinato" in lowered or "homicidio" in lowered:
            return [1.0, 0.0]
        return [0.0, 1.0]


def test_memory_retrieval_uses_configured_embedding_service():
    catalog = SourceCatalog()

    semantic_source = SourceRecord(
        source_id="source-semantic",
        document_id="doc-semantic",
        version_id="ver-semantic",
        title="Base semantica sobre homicidio",
        source_type=SourceType.LEGACY_SEED,
        authority=SourceAuthority.SECONDARY,
        is_official=False,
        is_primary=False,
        raw_text="Homicidio doloso com discussao sobre autoria e materialidade.",
        metadata=SourceMetadata(tema="Direito penal"),
    )
    semantic_chunk = ChunkRecord(
        chunk_id=stable_id("semantic", "homicidio"),
        source_id=semantic_source.source_id,
        document_id=semantic_source.document_id,
        version_id=semantic_source.version_id,
        title=semantic_source.title,
        content="Homicidio doloso com discussao sobre autoria e materialidade.",
        hierarchy=["penal"],
        source_type=SourceType.LEGACY_SEED,
        authority=SourceAuthority.SECONDARY,
        is_official=False,
        is_primary=False,
        metadata=semantic_source.metadata,
        hash=stable_id("semantic", "homicidio", "chunk"),
        embedding=[1.0, 0.0],
        search_text="Homicidio doloso autoria materialidade",
    )

    official_source = SourceRecord(
        source_id="source-official",
        document_id="doc-official",
        version_id="ver-official",
        title="Norma oficial irrelevante",
        source_type=SourceType.LEGISLATION,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        raw_text="Lei oficial sobre tema administrativo sem relacao semantica com a consulta.",
        metadata=SourceMetadata(numero_norma="Lei 1/2026"),
    )
    official_chunk = ChunkRecord(
        chunk_id=stable_id("official", "irrelevante"),
        source_id=official_source.source_id,
        document_id=official_source.document_id,
        version_id=official_source.version_id,
        title=official_source.title,
        content="Lei oficial sobre tema administrativo sem relacao semantica com a consulta.",
        hierarchy=["administrativo"],
        source_type=SourceType.LEGISLATION,
        authority=SourceAuthority.PRIMARY,
        is_official=True,
        is_primary=True,
        metadata=official_source.metadata,
        hash=stable_id("official", "irrelevante", "chunk"),
        embedding=[0.0, 1.0],
        search_text="Tema administrativo licenca funcionamento",
    )

    catalog.sources[semantic_source.source_id] = semantic_source
    catalog.sources[official_source.source_id] = official_source
    catalog.chunks[semantic_chunk.chunk_id] = semantic_chunk
    catalog.chunks[official_chunk.chunk_id] = official_chunk

    service = RetrievalService(catalog, embedding_service=StubEmbeddingService())
    results = service.search("Existe entendimento sobre assassinato doloso?", top_k=2, filters=RetrievalFilters())

    assert results
    assert results[0].chunk.title == "Base semantica sobre homicidio"
