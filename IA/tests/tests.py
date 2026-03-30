from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_consulta_artigo():
    response = client.get("/consulta?artigo=1")
    assert response.status_code == 200
    assert response.json()


def test_consulta_tema():
    response = client.get("/consulta?tema=trabalho")
    assert response.status_code == 200
    assert response.json()


def test_consulta_tipo_invalido():
    response = client.get("/consulta?tipo=invalido")
    assert response.status_code == 200
    assert response.json() == {
        "mensagem": "Tipo invalido. Use 'consulta', 'analise_situacao' ou 'analise_contrato'."
    }


def test_chat_query_alias():
    response = client.post("/api/v1/chat/query", json={"texto": "Quais sao os direitos trabalhistas?"})
    assert response.status_code == 200
    assert "resposta" in response.json()


def test_chat_query_preflight():
    response = client.options(
        "/api/v1/chat/query",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
