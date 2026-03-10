import pytest

pytest.importorskip("fastapi.testclient")

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_consulta_artigo():
    response = client.get("/consulta", params={"artigo": "1"})
    assert response.status_code == 200
    assert "resposta" in response.json()


def test_consulta_tema():
    response = client.get("/consulta", params={"tema": "trabalho"})
    assert response.status_code == 200
    assert "resposta" in response.json()


def test_perguntar():
    response = client.post("/perguntar", json={"texto": "Quais sao meus direitos como consumidor?"})
    assert response.status_code == 200
    assert "resposta" in response.json()
