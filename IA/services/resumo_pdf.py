import logging
import fitz  
import io
import re
  
from services.groq_client import gerar_resumo_groq

logging.basicConfig(level=logging.DEBUG)


def limpar_texto(texto: str) -> str:
    """Remove ruídos como numeração, símbolos e espaços excessivos."""
    texto = re.sub(r'\n+', ' ', texto)
    texto = re.sub(r'•|\-|–|—', ' ', texto)
    texto = re.sub(r'\d{1,3}\s*-\s*', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


def ler_pdf(file_obj) -> str:
    """Lê um arquivo PDF e retorna o texto limpo."""
    logging.debug(f"Lendo PDF: {file_obj}")
    try:
        file_bytes = file_obj.read() if hasattr(file_obj, "read") else file_obj
        pdf = fitz.open(stream=io.BytesIO(file_bytes), filetype="pdf")
        texto = ""
        for page in pdf:
            texto += page.get_text("text") + "\n"
        pdf.close()
        texto = limpar_texto(texto)
        logging.debug("Leitura do PDF concluída.")
        return texto
    except Exception as e:
        logging.error(f"Erro ao ler PDF: {e}")
        return ""


def eh_documento_juridico(texto: str) -> bool:
    """Detecta se o documento possui contexto jurídico."""
    palavras_chave = [
        "constituição", "lei", "direito", "jurídico", "cidadania", "tribunal",
        "justiça", "artigo", "constitucional", "advogado", "oab",
        "código civil", "penal", "jurisdição", "contrato", "obrigação",
        "cláusula", "acordo", "regulamento", "normas"
    ]
    texto_lower = texto.lower()
    return any(p in texto_lower for p in palavras_chave)




def gerar_resumo_pdf(file_obj) -> dict:
    """Extrai texto de um PDF e gera resumo via Groq."""
    texto = ler_pdf(file_obj)
    if not texto:
        return {"erro": "Não foi possível extrair texto do PDF."}

    tipo_resumo = "resumo de documento jurídico" if eh_documento_juridico(texto) else "resumo de documento geral"
    logging.info(f"Gerando resumo com Groq para '{tipo_resumo}'...")

    resumo = gerar_resumo_groq(texto, tipo=tipo_resumo)
    return {"resumo": resumo}
