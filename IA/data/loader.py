import json
from pathlib import Path
from typing import List, Dict

DATA_DIR = Path(__file__).parent.parent / "data"

def carregar_dados_json(caminho: Path) -> List[Dict]:
    """
    Carrega dados de um arquivo JSON especificado pelo caminho.

    Args:
        caminho (Path): O caminho completo para o arquivo JSON.

    Returns:
        List[Dict]: Uma lista de dicionários contendo os dados do JSON, ou uma lista vazia em caso de erro.
    """
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em {caminho}")
        return []
    except json.JSONDecodeError:
        print(f"Erro: Problema ao decodificar JSON em {caminho}. Verifique a formatação do arquivo.")
        return []

def segmentar_texto(texto: str, tamanho_max: int = 300) -> List[str]:
    """
    Segmenta um texto longo em blocos menores para busca semântica.

    Args:
        texto (str): Texto completo.
        tamanho_max (int): Número máximo de caracteres por bloco.

    Returns:
        List[str]: Lista de blocos de texto.
    """
    blocos = []
    palavras = texto.split()
    bloco_atual = []

    for palavra in palavras:
        bloco_atual.append(palavra)
        if len(" ".join(bloco_atual)) >= tamanho_max:
            blocos.append(" ".join(bloco_atual))
            bloco_atual = []

    if bloco_atual:
        blocos.append(" ".join(bloco_atual))

    return blocos

def carregar_base_segmentada(caminho: Path, tipo: str) -> List[Dict]:
    """
    Carrega dados do JSON e os segmenta em blocos menores.

    Args:
        caminho (Path): Caminho do arquivo JSON.
        tipo (str): Tipo do dado (consulta, situacao, contrato).

    Returns:
        List[Dict]: Lista de blocos segmentados com metadados.
    """
    dados = carregar_dados_json(caminho)
    base_segmentada = []

    for item in dados:
        texto = item.get("texto", "")
        topico = item.get("tema", item.get("titulo", ""))
        blocos = segmentar_texto(texto)
        for idx, bloco in enumerate(blocos):
            base_segmentada.append({
                "id": f"{item.get('id', idx)}_{idx}",
                "tipo": tipo,
                "tema": topico,
                "texto": bloco,
                "original": texto,
            })

    return base_segmentada

def carregar_artigos() -> List[Dict]:
    """Carrega artigos jurídicos segmentados."""
    return carregar_base_segmentada(DATA_DIR / "base_juridica.json", "consulta")

def carregar_situacoes() -> List[Dict]:
    """Carrega situações jurídicas segmentadas."""
    return carregar_base_segmentada(DATA_DIR / "situacoes.json", "analise_situacao")

def carregar_contratos() -> List[Dict]:
    """Carrega contratos segmentados."""
    return carregar_base_segmentada(DATA_DIR / "contratos.json", "analise_contrato")
