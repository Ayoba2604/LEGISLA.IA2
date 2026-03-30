from typing import Dict, List

from data.loader import carregar_artigos, carregar_contratos, carregar_situacoes


def _contem_termo(valor: object, termo: str) -> bool:
    return termo in str(valor or "").lower()


def buscar_por_artigo(artigo: str, tipo: str = "consulta") -> List[Dict]:
    termo = (artigo or "").strip().lower()
    if not termo:
        return []

    dados = _carregar_dados_por_tipo(tipo)
    return [
        item
        for item in dados
        if any(
            _contem_termo(item.get(campo), termo)
            for campo in ("artigo", "id", "titulo", "tema", "descricao")
        )
    ]


def buscar_por_tema(tema: str, tipo: str = "consulta") -> List[Dict]:
    termo = (tema or "").strip().lower()
    if not termo:
        return []

    dados = _carregar_dados_por_tipo(tipo)
    return [
        item
        for item in dados
        if any(
            _contem_termo(item.get(campo), termo)
            for campo in ("tema", "titulo", "descricao", "texto", "analise", "original")
        )
    ]


def _carregar_dados_por_tipo(tipo: str) -> List[Dict]:
    if tipo == "consulta":
        return carregar_artigos()
    if tipo == "analise_situacao":
        return carregar_situacoes()
    if tipo == "analise_contrato":
        return carregar_contratos()
    return []
