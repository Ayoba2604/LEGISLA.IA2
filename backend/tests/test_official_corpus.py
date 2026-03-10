import json

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
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "backend.app.connectors.official_corpus.fetch_remote_payload",
        lambda url: (b"<html><body>Art. 1. Norma oficial de teste.</body></html>", "text/html"),
    )

    builder = OfficialCorpusBuilder(session=FakeSession())
    report = builder.build_from_registry_file(
        registry_path=registry_path,
        manifest_output_path=manifest_path,
        snapshot_root=snapshot_root,
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert report.collected_sources == 2
    assert report.failed_sources == 0
    assert len(manifest) == 2
    assert manifest[0]["source_type"] == "legislation"
    assert manifest[1]["source_type"] == "jurisprudence"
    assert snapshot_root.joinpath("planalto").exists()
    assert snapshot_root.joinpath("stj", "espelhos-de-acordaos-primeira-turma").exists()

