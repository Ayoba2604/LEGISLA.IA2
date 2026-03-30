import json
from pathlib import Path
from typing import Dict, List

DATA_DIR = Path(__file__).resolve().parent


def carregar_dados_json(caminho: Path) -> List[Dict]:
    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except FileNotFoundError:
        print(f"Erro: arquivo nao encontrado em {caminho}")
        return []
    except json.JSONDecodeError:
        print(f"Erro: JSON invalido em {caminho}")
        return []

    return dados if isinstance(dados, list) else []


def segmentar_texto(texto: str, tamanho_max: int = 300) -> List[str]:
    texto = (texto or "").strip()
    if not texto:
        return []

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


def _texto_para_busca(item: Dict) -> str:
    campos = (
        "artigo",
        "tema",
        "titulo",
        "descricao",
        "texto",
        "explicacao",
        "analise",
        "tipo",
    )
    return " ".join(str(item.get(campo, "")).strip() for campo in campos if item.get(campo))


def carregar_base_segmentada(caminho: Path, categoria: str) -> List[Dict]:
    dados = carregar_dados_json(caminho)
    base_segmentada = []

    for item in dados:
        texto_integral = _texto_para_busca(item)
        blocos = segmentar_texto(texto_integral) or [texto_integral]

        for idx, bloco in enumerate(blocos):
            base_segmentada.append(
                {
                    **item,
                    "categoria": categoria,
                    "tema": item.get("tema") or item.get("titulo") or item.get("descricao", ""),
                    "texto": bloco,
                    "original": texto_integral,
                    "chunk_id": idx,
                }
            )

    return base_segmentada


def carregar_artigos() -> List[Dict]:
    return carregar_base_segmentada(DATA_DIR / "base_juridica.json", "consulta")


def carregar_situacoes() -> List[Dict]:
    return carregar_base_segmentada(DATA_DIR / "situacoes.json", "analise_situacao")


def carregar_contratos() -> List[Dict]:
    return carregar_base_segmentada(DATA_DIR / "contratos.json", "analise_contrato")
