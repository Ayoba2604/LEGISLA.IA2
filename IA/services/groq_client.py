import logging
import os
from typing import Optional

from groq import Groq

from env_loader import load_project_env


logger = logging.getLogger(__name__)
load_project_env()


def _get_client() -> Optional[Groq]:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        logger.warning("GROQ_API_KEY nao configurada; usando fallback local.")
        return None
    return Groq(api_key=api_key)


def gerar_resposta_groq(pergunta: str, base_dados: list | None = None) -> str:
    client = _get_client()
    if client is None:
        return ""
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip() or "llama-3.1-8b-instant"

    contexto = ""
    for item in base_dados or []:
        contexto += f"{item}\n"

    prompt = (
        "Voce e uma assistente juridica virtual. Use o contexto abaixo quando ele "
        "for relevante e responda de forma clara, objetiva e educada.\n\n"
        f"Contexto:\n{contexto or 'Sem contexto adicional.'}\n\n"
        f"Pergunta do usuario: {pergunta}"
    )

    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
        )
    except Exception as exc:
        logger.error("Erro ao gerar resposta com Groq: %s", exc, exc_info=True)
        return ""

    mensagem = getattr(response.choices[0].message, "content", "")
    return mensagem.strip() if mensagem else ""


def gerar_resumo_groq(texto: str, tipo: str = "resumo") -> str:
    client = _get_client()
    if client is None:
        return "Servico de IA indisponivel no momento."
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip() or "llama-3.1-8b-instant"

    prompt = (
        "Voce e uma IA juridica experiente. Analise o conteudo abaixo e produza "
        f"uma resposta em portugues no formato de {tipo}.\n\n"
        f"Conteudo:\n{texto}"
    )

    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.2,
        )
    except Exception as exc:
        logger.error("Erro no Groq: %s", exc, exc_info=True)
        return "Nao foi possivel gerar a resposta com o servico de IA."

    mensagem = getattr(response.choices[0].message, "content", "")
    return mensagem.strip() if mensagem else "Nao foi possivel gerar a resposta."


def gerar_resposta_generica_groq(texto: str) -> str:
    return gerar_resumo_groq(texto, tipo="resposta")
