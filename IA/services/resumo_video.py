import logging
import re
from typing import List, Optional
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from services import groq_client  
from services.groq_client import gerar_resumo_groq


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')




def obter_transcricao_youtube(video_url: str, idiomas_preferidos: Optional[List[str]] = None) -> Optional[str]:
    """Obtém a transcrição de um vídeo do YouTube."""
    if idiomas_preferidos is None:
        idiomas_preferidos = ["pt-BR", "pt", "en"]

    logging.debug(f"Tentando obter transcrição para: {video_url} nos idiomas {idiomas_preferidos}")
    try:
        video_id = _extrair_video_id(video_url)
        for idioma in idiomas_preferidos:
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[idioma])
                texto = " ".join(t['text'] for t in transcript if t['text'].strip())
                if texto:
                    logging.debug(f"Transcrição encontrada com sucesso no idioma: {idioma}")
                    return texto
            except NoTranscriptFound:
                logging.debug(f"Sem transcrição para '{idioma}'.")
            except TranscriptsDisabled:
                logging.warning(f"Transcrição desabilitada para '{video_id}'.")
                return None
        logging.warning(f"Nenhuma transcrição disponível para '{video_id}'.")
        return None
    except ValueError as ve:
        logging.error(f"Erro ao extrair ID do vídeo: {ve}")
        return None
    except Exception as e:
        logging.error(f"Erro inesperado ao obter transcrição: {e}", exc_info=True)
        return None

def _extrair_video_id(url: str) -> str:
    """Extrai o ID do vídeo de uma URL do YouTube."""
    match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    if match:
        return match.group(1)
    raise ValueError("URL do YouTube inválida.")


def eh_video_juridico(texto: str) -> bool:
    """Detecta se o vídeo possui contexto jurídico."""
    palavras_chave = [
        "constituição", "lei", "direito", "jurídico", "cidadania", "tribunal",
        "justiça", "artigo", "constitucional", "advogado", "oab", "código civil",
        "supremo", "stf", "stj", "penal", "civil", "processo", "legal", "norma",
        "jurisprudência", "decisão", "ação judicial", "magistrado", "procurador"
    ]
    return any(p in texto.lower() for p in palavras_chave)


def gerar_resumo_video(url_video: str) -> str:
    """
    Obtém a transcrição do vídeo e gera um resumo usando SOMENTE o groq_client centralizado.
    """
    transcricao = obter_transcricao_youtube(url_video)
    if not transcricao:
        return ":(   Não foi possível obter a transcrição deste vídeo."

    tipo_resumo = "resumo de vídeo jurídico" if eh_video_juridico(transcricao) else "resumo de vídeo geral"
    logging.info(f"Gerando resumo com Groq para '{tipo_resumo}'...")

    resumo = gerar_resumo_groq(transcricao, tipo=tipo_resumo)
    if resumo and not resumo.startswith("⚠️"):
        logging.info("Resumo gerado com sucesso pelo Groq.")
        return resumo

    logging.error("Falha ao gerar resumo pelo Groq.")
    return "❌ Não foi possível gerar o resumo do vídeo."


if __name__ == "__main__":
    url_exemplo_geral = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    url_exemplo_sem_transcricao = "https://www.youtube.com/watch?v=c0T_0bH-lYc"

    print("\n--- Teste com Vídeo Geral ---")
    print(gerar_resumo_video(url_exemplo_geral))

    print("\n--- Teste com Vídeo sem Transcrição ---")
    print(gerar_resumo_video(url_exemplo_sem_transcricao))



def gerar_resumo_video(url_video: str) -> str:
    transcricao = obter_transcricao_youtube(url_video)
    if not transcricao:
        return ":(   Não foi possível obter a transcrição deste vídeo."
    tipo = "resumo de vídeo jurídico" if eh_video_juridico(transcricao) else "resumo de vídeo geral"
    return gerar_resumo_groq(transcricao, tipo)


