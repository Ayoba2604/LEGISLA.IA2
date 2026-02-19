import re
import unicodedata
import logging
from services.groq_client import gerar_resposta_generica_groq

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
    """
    Gera a resposta usando Groq.
    Sempre considera que o modelo é uma IA jurídica.
    """
    texto_norm = normalizar_texto(texto)
    try:
        prompt = f"""
        Você é uma assistente jurídica virtual, especializada em direito brasileiro. 
        Seu papel é responder de forma clara, educada e objetiva, adaptando o tom de acordo com a situação:

        1. Se o usuário fizer uma saudação ou comentário informal (como "oi", "olá", "como vai?"), responda cordialmente de forma breve e amigável.
        2. Se o usuário fizer uma pergunta jurídica, forneça uma resposta detalhada, explicativa e precisa, baseada na legislação brasileira.
        3. Sempre use linguagem acessível e clara, evitando termos excessivamente técnicos quando possível.
        4. Se não houver informações suficientes para responder juridicamente, explique de forma educada que precisa de mais contexto.

        Pergunta do usuário: "{texto_norm}"
        Responda como uma assistente jurídica virtual profissional, mantendo-se clara, objetiva e cordial.
        """
        resposta = gerar_resposta_generica_groq(prompt)
        return resposta.strip()
    except Exception as e:
        logging.error(f"Erro ao gerar resposta com Groq: {e}")
        return "Desculpe, não consegui processar sua pergunta no momento."
