import pytest

pytest.importorskip("fastapi.testclient")

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_legacy_consulta_endpoint():
    response = client.get("/consulta", params={"tema": "trabalho"})
    assert response.status_code == 200
    assert "resposta" in response.json()
