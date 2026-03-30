import logging
import re
from typing import List, Optional

from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled, YouTubeTranscriptApi

from services.gemini_client import gerar_resumo_gemini


logger = logging.getLogger(__name__)


def obter_transcricao_youtube(
    video_url: str, idiomas_preferidos: Optional[List[str]] = None
) -> Optional[str]:
    if idiomas_preferidos is None:
        idiomas_preferidos = ["pt-BR", "pt", "en"]

    try:
        video_id = _extrair_video_id(video_url)
    except ValueError as exc:
        logger.error("Erro ao extrair ID do video: %s", exc)
        return None

    for idioma in idiomas_preferidos:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[idioma])
        except NoTranscriptFound:
            continue
        except TranscriptsDisabled:
            logger.warning("Transcricao desabilitada para o video %s", video_id)
            return None
        except Exception as exc:
            logger.error("Erro ao buscar transcricao: %s", exc, exc_info=True)
            return None

        texto = " ".join(trecho["text"] for trecho in transcript if trecho["text"].strip())
        if texto:
            return texto

    logger.warning("Nenhuma transcricao disponivel para o video %s", video_id)
    return None


def _extrair_video_id(url: str) -> str:
    match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    if match:
        return match.group(1)
    raise ValueError("URL do YouTube invalida.")


def eh_video_juridico(texto: str) -> bool:
    palavras_chave = [
        "constituicao",
        "lei",
        "direito",
        "juridico",
        "cidadania",
        "tribunal",
        "justica",
        "artigo",
        "constitucional",
        "advogado",
        "oab",
        "codigo civil",
        "supremo",
        "stf",
        "stj",
        "penal",
        "civil",
        "processo",
        "norma",
        "jurisprudencia",
    ]
    texto_lower = (texto or "").lower()
    return any(palavra in texto_lower for palavra in palavras_chave)


def gerar_resumo_video(url_video: str) -> str:
    transcricao = obter_transcricao_youtube(url_video)
    if not transcricao:
        return "Nao foi possivel obter a transcricao deste video."

    tipo = "resumo de video juridico" if eh_video_juridico(transcricao) else "resumo de video geral"
    resumo = gerar_resumo_gemini(transcricao, tipo)
    return resumo or "Nao foi possivel gerar o resumo do video."
