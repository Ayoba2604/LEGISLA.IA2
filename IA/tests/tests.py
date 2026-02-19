
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 404 # Endpoint não existe, esperado 404

def test_consulta_artigo():
    response = client.get("/consulta?artigo=1")
    assert response.status_code == 200

def test_consulta_tema():
    response = client.get("/consulta?tema=trabalho")
    assert response.status_code == 200

def test_consulta_tipo_invalido():
    response = client.get("/consulta?tipo=invalido")
    assert response.status_code == 200
    assert response.json() == {"mensagem": "Tipo inválido. Use 'consulta', 'analise_situacao' ou 'analise_contrato'."}


