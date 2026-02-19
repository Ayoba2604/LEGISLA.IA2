from data.loader import carregar_artigos, carregar_situacoes, carregar_contratos
from typing import Optional, List, Dict

def buscar_por_artigo(artigo: str, tipo: str = "consulta") -> List[Dict]:
    dados = _carregar_dados_por_tipo(tipo)
    return [item for item in dados if artigo.lower() in item.get("artigo", "").lower()]

def buscar_por_tema(tema: str, tipo: str = "consulta") -> List[Dict]:
    dados = _carregar_dados_por_tipo(tipo)
    return [item for item in dados if tema.lower() in item.get("tema", "").lower()]

def _carregar_dados_por_tipo(tipo: str) -> List[Dict]:
    if tipo == "consulta":
        return carregar_artigos()
    elif tipo == "analise_situacao":
        return carregar_situacoes()
    elif tipo == "analise_contrato":
        return carregar_contratos()
    return []

