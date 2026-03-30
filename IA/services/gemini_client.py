import logging
import os
from typing import Optional

from google import genai
from google.genai import types

from env_loader import load_project_env

logger = logging.getLogger(__name__)
load_project_env()

_client: Optional[genai.Client] = None

# Modelo principal para chat (500 RPD - maior quota)
MODEL_CHAT = "gemini-3.1-flash-lite-preview"
# Modelo para analise conclusiva e tarefas que exigem mais raciocinio (20 RPD)
MODEL_ANALISE = "gemini-3-flash-preview"
# Modelo para resumos de PDF/video (20 RPD)
MODEL_RESUMO = "gemini-2.5-flash"
# Fallback caso algum modelo esteja indisponivel
MODEL_FALLBACK = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = (
    "Voce e a Legisla.IA, uma assistente juridica virtual especializada em direito brasileiro. "
    "Voce possui conhecimento aprofundado sobre:\n"
    "- Constituicao Federal de 1988 (todos os artigos e emendas)\n"
    "- Codigo Civil (Lei 10.406/2002)\n"
    "- Codigo Penal (Decreto-Lei 2.848/1940)\n"
    "- Codigo de Defesa do Consumidor (Lei 8.078/1990)\n"
    "- CLT - Consolidacao das Leis do Trabalho\n"
    "- Codigo de Processo Civil e Penal\n"
    "- Estatuto da Crianca e do Adolescente (ECA)\n"
    "- Lei de Locacoes (Lei 8.245/91)\n"
    "- Lei Maria da Penha, Marco Civil da Internet, LGPD\n"
    "- Jurisprudencia dos tribunais superiores (STF, STJ, TST)\n"
    "- Sumulas vinculantes e orientacoes jurisprudenciais\n\n"
    "REGRAS DE RESPOSTA:\n"
    "1. Sempre cite os artigos de lei, paragrafos e incisos especificos quando responder.\n"
    "2. Use seu proprio conhecimento juridico como fonte principal. O contexto local fornecido "
    "e apenas complementar — se ele for vago ou insuficiente, IGNORE-O e responda com base "
    "no seu conhecimento.\n"
    "3. Estruture respostas com titulos em negrito (**Titulo**), listas e separadores.\n"
    "4. Explique os termos juridicos em linguagem acessivel.\n"
    "5. Quando relevante, mencione prazos, procedimentos e a qual orgao recorrer.\n"
    "6. Se a pergunta for uma saudacao ou conversa casual, responda de forma breve e cordial.\n"
    "7. Se nao tiver certeza sobre algo, diga explicitamente e recomende consultar um advogado.\n"
    "8. Responda sempre em portugues brasileiro."
)


def _get_client() -> Optional[genai.Client]:
    global _client
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        logger.warning("GEMINI_API_KEY nao configurada; usando fallback local.")
        return None
    if _client is None:
        _client = genai.Client(api_key=api_key)
    return _client


def _chamar_modelo(client: genai.Client, model: str, prompt: str, temperature: float = 0.4) -> str:
    """Chama o modelo com fallback automatico se o principal falhar."""
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=temperature,
            ),
        )
        texto = response.text or ""
        return texto.strip()
    except Exception as exc:
        logger.warning("Modelo %s falhou: %s — tentando fallback %s", model, exc, MODEL_FALLBACK)
        if model == MODEL_FALLBACK:
            raise
        response = client.models.generate_content(
            model=MODEL_FALLBACK,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=temperature,
            ),
        )
        texto = response.text or ""
        return texto.strip()


def gerar_resposta_gemini(pergunta: str, base_dados: list | None = None, modelo: str | None = None) -> str:
    client = _get_client()
    if client is None:
        return ""

    model = modelo or MODEL_CHAT

    contexto = ""
    for item in base_dados or []:
        contexto += f"{item}\n"

    if contexto.strip():
        prompt = (
            f"Pergunta do usuario: {pergunta}\n\n"
            f"Contexto complementar da base local (use apenas se for relevante):\n{contexto}"
        )
    else:
        prompt = f"Pergunta do usuario: {pergunta}"

    try:
        return _chamar_modelo(client, model, prompt)
    except Exception as exc:
        logger.error("Erro ao gerar resposta com Gemini: %s", exc, exc_info=True)
        return ""


def gerar_resumo_gemini(texto: str, tipo: str = "resumo", modelo: str | None = None) -> str:
    client = _get_client()
    if client is None:
        return "Servico de IA indisponivel no momento."

    model = modelo or MODEL_RESUMO

    prompt = (
        f"Analise o conteudo abaixo e produza uma resposta em portugues no formato de {tipo}. "
        "Seja detalhado, cite artigos de lei quando aplicavel e estruture com titulos e listas.\n\n"
        f"Conteudo:\n{texto}"
    )

    try:
        return _chamar_modelo(client, model, prompt, temperature=0.2)
    except Exception as exc:
        logger.error("Erro no Gemini: %s", exc, exc_info=True)
        return "Nao foi possivel gerar a resposta com o servico de IA."


def gerar_resposta_generica_gemini(texto: str) -> str:
    return gerar_resumo_gemini(texto, tipo="resposta")
