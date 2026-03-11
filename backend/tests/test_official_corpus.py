import json

from backend.app.connectors.models import DataJudQuerySpec
from backend.app.connectors.official_corpus import OfficialCorpusBuilder


class FakeResponse:
    def __init__(self, payload, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self):
        self.headers = {}

    def request(self, method, url, json=None, headers=None, timeout=None, verify=None):
        if "package_show" in url:
            return FakeResponse(
                {
                    "result": {
                        "title": "Espelhos de acordaos - Primeira Turma",
                        "resources": [
                            {
                                "format": "JSON",
                                "url": "https://dadosabertos.web.stj.jus.br/resource/latest.json",
                                "created": "2025-01-31T00:00:00",
                            }
                        ],
                    }
                }
            )
        if url == "https://dadosabertos.web.stj.jus.br/resource/latest.json":
            return FakeResponse(
                [
                    {
                        "id": "0001",
                        "numeroProcesso": "123",
                        "numeroRegistro": "202500000001",
                        "siglaClasse": "REsp",
                        "descricaoClasse": "RECURSO ESPECIAL",
                        "nomeOrgaoJulgador": "PRIMEIRA TURMA",
                        "ministroRelator": "MINISTRO TESTE",
                        "dataPublicacao": "DJE DATA:31/01/2025",
                        "ementa": "EMENTA DE TESTE.",
                        "tipoDeDecisao": "ACORDAO",
                        "dataDecisao": "20250130",
                        "decisao": "DECISAO DE TESTE.",
                        "referenciasLegislativas": ["CDC, art. 14"],
                    }
                ]
            )
        raise AssertionError(f"Unexpected URL: {url}")


def fake_remote_payload(url: str):
    if "planalto" in url:
        return b"<html><body>Art. 1. Norma oficial de teste.</body></html>", "text/html"
    return (
        (
            "Sumula 297 do STJ. O Codigo de Defesa do Consumidor e aplicavel as instituicoes financeiras.\n"
            "Sumula 479 do STJ. As instituicoes financeiras respondem objetivamente por danos internos relativos a fraudes."
        ).encode("utf-8"),
        "text/plain",
    )


def fake_remote_payload_sumula_fallback(url: str):
    if "fallback" not in url:
        return b"<html><body>Catalogo institucional sem sumulas.</body></html>", "text/html"
    return (
        (
            "Sumula 297 do STJ. O Codigo de Defesa do Consumidor e aplicavel as instituicoes financeiras.\n"
            "Sumula 479 do STJ. As instituicoes financeiras respondem objetivamente por danos internos relativos a fraudes."
        ).encode("utf-8"),
        "text/plain",
    )


def test_official_corpus_builder_generates_manifest(tmp_path, monkeypatch):
    registry_path = tmp_path / "official_registry.json"
    manifest_path = tmp_path / "manifest.json"
    snapshot_root = tmp_path / "snapshots"
    registry_path.write_text(
        json.dumps(
            {
                "snapshot_root": str(snapshot_root),
                "manifest_output_path": str(manifest_path),
                "planalto_legislation": [
                    {
                        "title": "Constituicao Federal",
                        "url": "https://www.planalto.gov.br/ccivil_03/Constituicao/ConstituicaoCompilado.htm",
                        "numero_norma": "Constituicao Federal de 1988",
                        "tipo_norma": "constituicao",
                    }
                ],
                "stj_open_data": [
                    {
                        "package_name": "espelhos-de-acordaos-primeira-turma",
                        "max_records": 1,
                    }
                ],
                "official_sumulas": [
                    {
                        "title": "Sumulas do STJ",
                        "tribunal": "STJ",
                        "url": "https://www.stj.jus.br/docs_internet/SumulasSTJ.pdf",
                        "fallback_urls": [
                            "https://bdjur.stj.jus.br/jspui/bitstream/2011/113497/sumulas_stj.pdf"
                        ],
                        "mime_type": "text/plain",
                        "max_entries": 2
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "backend.app.connectors.official_corpus.fetch_remote_payload",
        fake_remote_payload,
    )

    builder = OfficialCorpusBuilder(session=FakeSession())
    report = builder.build_from_registry_file(
        registry_path=registry_path,
        manifest_output_path=manifest_path,
        snapshot_root=snapshot_root,
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert report.collected_sources == 4
    assert report.failed_sources == 0
    assert len(manifest) == 4
    assert manifest[0]["source_type"] == "legislation"
    assert manifest[1]["source_type"] == "jurisprudence"
    assert manifest[2]["source_type"] == "sumula"
    assert snapshot_root.joinpath("planalto").exists()
    assert snapshot_root.joinpath("stj", "espelhos-de-acordaos-primeira-turma").exists()
    assert snapshot_root.joinpath("sumulas", "stj").exists()


def test_official_sumula_builder_uses_fallback_url_when_primary_has_no_entries(tmp_path, monkeypatch):
    registry_path = tmp_path / "official_registry.json"
    manifest_path = tmp_path / "manifest.json"
    snapshot_root = tmp_path / "snapshots"
    registry_path.write_text(
        json.dumps(
            {
                "snapshot_root": str(snapshot_root),
                "manifest_output_path": str(manifest_path),
                "official_sumulas": [
                    {
                        "title": "Sumulas do STJ",
                        "tribunal": "STJ",
                        "url": "https://publicacao-invalida.example/sumulas.html",
                        "fallback_urls": [
                            "https://fallback.example/SumulasSTJ.pdf"
                        ],
                        "mime_type": "text/plain",
                        "max_entries": 1
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "backend.app.connectors.official_corpus.fetch_remote_payload",
        fake_remote_payload_sumula_fallback,
    )

    builder = OfficialCorpusBuilder(session=FakeSession())
    report = builder.build_from_registry_file(
        registry_path=registry_path,
        manifest_output_path=manifest_path,
        snapshot_root=snapshot_root,
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert report.collected_sources == 1
    assert report.failed_sources == 0
    assert manifest[0]["metadata"]["url_origem"] == "https://fallback.example/SumulasSTJ.pdf"
    assert "publication_url_requested" in manifest[0]["metadata"]["metadata_extra"]


def test_datajud_payload_supports_incremental_range():
    payload = OfficialCorpusBuilder._build_datajud_payload(
        DataJudQuerySpec(
            name="datajud-test",
            endpoint="https://api-publica.datajud.cnj.jus.br/api_publica_tj/_search",
            updated_since_days=15,
            payload={
                "size": 10,
                "query": {
                    "match": {
                        "classe.nome": "consumidor"
                    }
                },
            },
        )
    )

    assert payload["query"]["bool"]["must"][0]["match"]["classe.nome"] == "consumidor"
    assert payload["query"]["bool"]["filter"][0]["range"]["dataHoraUltimaAtualizacao"]["gte"]
