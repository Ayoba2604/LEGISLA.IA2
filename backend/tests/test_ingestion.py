import json

from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.services.source_catalog import SourceCatalog


def test_ingestion_generates_chunks():
    pipeline = IngestionPipeline()
    source, chunks, warnings, injection = pipeline.ingest_upload(
        filename="contrato.txt",
        mime_type="text/plain",
        payload=b"CLAUSULA 1. O LOCATARIO pagara o aluguel mensal. CLAUSULA 2. O reajuste seguira o indice previsto.",
    )

    assert source.source_id
    assert chunks
    assert isinstance(warnings, list)
    assert injection is False


def test_manifest_ingestion_imports_local_sources(tmp_path):
    source_path = tmp_path / "lei.txt"
    source_path.write_text("Art. 1. Esta norma de teste esta vigente.", encoding="utf-8")
    manifest_path = tmp_path / "corpus_manifest.json"
    manifest_path.write_text(
        json.dumps(
            [
                {
                    "title": "Norma de teste",
                    "source_type": "legislation",
                    "authority": "primary",
                    "path": str(source_path),
                    "is_official": True,
                    "is_primary": True,
                    "metadata": {
                        "numero_norma": "Lei 9999/2026",
                        "vigencia": "vigente",
                    },
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    pipeline = IngestionPipeline()
    catalog = SourceCatalog()
    report = pipeline.ingest_manifest(manifest_path=manifest_path, catalog=catalog, persist=False)

    assert report.imported_sources == 1
    assert report.imported_chunks >= 1
    assert report.source_ids
    assert any(source.source_type.value == "legislation" for source in catalog.sources.values())


def test_legislation_chunking_extracts_article_and_hierarchy(tmp_path):
    source_path = tmp_path / "norma.txt"
    source_path.write_text(
        "\n".join(
            [
                "LEI 9.999/2026",
                "TITULO I",
                "Direitos fundamentais de teste",
                "CAPITULO I",
                "Garantias",
                "Art. 1. Esta lei estabelece regras de teste.",
                "§ 1o Aplicam-se disposicoes complementares.",
                "Art. 2. Esta lei entra em vigor na data de sua publicacao.",
            ]
        ),
        encoding="utf-8",
    )
    manifest_path = tmp_path / "corpus_manifest.json"
    manifest_path.write_text(
        json.dumps(
            [
                {
                    "title": "Lei de teste estruturada",
                    "source_type": "legislation",
                    "authority": "primary",
                    "path": str(source_path),
                    "is_official": True,
                    "is_primary": True,
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    pipeline = IngestionPipeline()
    catalog = SourceCatalog()
    report = pipeline.ingest_manifest(manifest_path=manifest_path, catalog=catalog, persist=False)

    assert report.imported_sources == 1
    article_chunks = [chunk for chunk in catalog.list_chunks() if chunk.metadata.artigo]
    assert article_chunks
    assert article_chunks[0].title.endswith("Art. 1")
    assert article_chunks[0].metadata.titulo_normativo == "TITULO I"
    assert article_chunks[0].metadata.capitulo == "CAPITULO I"
    assert article_chunks[0].metadata.paragrafo
    assert "art. 1" in article_chunks[0].hierarchy


def test_jurisprudence_chunking_extracts_sections_and_metadata(tmp_path):
    source_path = tmp_path / "acordao.txt"
    source_path.write_text(
        "\n".join(
            [
                "TRIBUNAL: Superior Tribunal de Justica",
                "ORGAO JULGADOR: TERCEIRA TURMA",
                "NUMERO DO PROCESSO: REsp 123456/DF",
                "RELATOR: MINISTRA TESTE",
                "DATA DA DECISAO: 20250130",
                "EMENTA:",
                "Responsabilidade civil por defeito na prestacao do servico.",
                "TESE JURIDICA:",
                "O defeito relevante na prestacao do servico gera dever de indenizar.",
                "DECISAO:",
                "Recurso especial provido.",
            ]
        ),
        encoding="utf-8",
    )
    manifest_path = tmp_path / "corpus_manifest.json"
    manifest_path.write_text(
        json.dumps(
            [
                {
                    "title": "Acordao de teste",
                    "source_type": "jurisprudence",
                    "authority": "primary",
                    "path": str(source_path),
                    "is_official": True,
                    "is_primary": True,
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    pipeline = IngestionPipeline()
    catalog = SourceCatalog()
    pipeline.ingest_manifest(manifest_path=manifest_path, catalog=catalog, persist=False)

    chunks = catalog.list_chunks()
    ementa_chunk = next(chunk for chunk in chunks if chunk.metadata.metadata_extra.get("jurisprudencia_secao") == "ementa")
    tese_chunk = next(chunk for chunk in chunks if chunk.metadata.metadata_extra.get("jurisprudencia_secao") == "tese juridica")

    assert ementa_chunk.metadata.tribunal == "Superior Tribunal de Justica"
    assert ementa_chunk.metadata.orgao_julgador == "TERCEIRA TURMA"
    assert ementa_chunk.metadata.numero_processo == "REsp 123456/DF"
    assert ementa_chunk.metadata.relator == "MINISTRA TESTE"
    assert tese_chunk.metadata.tese_juridica.startswith("O defeito relevante")
