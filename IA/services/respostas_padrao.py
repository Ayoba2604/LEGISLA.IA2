import re
import unicodedata
import logging
from services.gemini_client import gerar_resposta_generica_gemini

def normalizar_texto(texto: str) -> str:
    """
    Normaliza o texto:
    - minúsculas
    - remove acentos
    - remove pontuação
    - remove espaços extras
    """
    texto = texto.lower().strip()
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    texto = re.sub(r'[^\w\s]', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto

def gerar_resposta(texto: str) -> str:
    """Gera a resposta usando Gemini com system instruction."""
    try:
        resposta = gerar_resposta_generica_gemini(texto)
        return resposta.strip()
    except Exception as e:
        logging.error(f"Erro ao gerar resposta com Gemini: {e}")
        return "Desculpe, nao consegui processar sua pergunta no momento."
