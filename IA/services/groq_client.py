"""Legacy compatibility wrappers for the old Groq integration."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.services.llm_service import LegalLLMService

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
_llm_service = LegalLLMService()


def gerar_resposta_groq(pergunta: str, base_dados: list | None = None) -> str:
    contexto = ""
    if base_dados:
        contexto = "\n".join(str(item) for item in base_dados)
    merged = f"{pergunta}\n\nContexto:\n{contexto}".strip()
    return _llm_service.summarize_text(merged, mode="resposta jurídica")


def gerar_resumo_groq(texto: str, tipo: str = "resumo") -> str:
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY não configurada; usando fallback local.")
    return _llm_service.summarize_text(texto, mode=tipo)


def gerar_resposta_generica_groq(texto: str) -> str:
    return gerar_resumo_groq(texto, tipo="resposta teste")
