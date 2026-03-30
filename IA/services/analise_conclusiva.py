import logging

import spacy

from services.gemini_client import gerar_resumo_gemini, MODEL_ANALISE

logger = logging.getLogger(__name__)

try:
    nlp = spacy.load("pt_core_news_sm")
except OSError:
    import spacy.cli
    spacy.cli.download("pt_core_news_sm")
    nlp = spacy.load("pt_core_news_sm")


def detectar_clausulas_abusivas(texto: str) -> list:
    """Identifica possíveis cláusulas leoninas ou abusivas no texto."""
    clausulas_suspeitas = [
        "renúncia de direitos",
        "indenização desproporcional",
        "multa excessiva",
        "exclusão de responsabilidade",
        "obrigações excessivas",
        "cláusula abusiva",
        "renuncia ao direito",
        "cláusula penal",
        "perda de direitos",
        "indenização sem culpa"
    ]
    texto_lower = texto.lower()
    encontradas = [c for c in clausulas_suspeitas if c in texto_lower]
    return encontradas


def gerar_conclusao_critica(texto: str) -> str:
    """Gera uma conclusao critica usando Gemini 3 Flash."""
    clausulas = detectar_clausulas_abusivas(texto)
    doc = nlp(texto)
    total_tokens = len([t for t in doc if not t.is_punct])

    info_clausulas = ""
    if clausulas:
        info_clausulas = (
            "\n\nClausulas potencialmente abusivas detectadas por analise automatica:\n"
            + "\n".join(f"- {c}" for c in clausulas)
        )

    prompt = (
        "Voce e um advogado especialista em direito contratual brasileiro. "
        "Analise criticamente o contrato abaixo e produza uma analise conclusiva detalhada. "
        "Identifique clausulas abusivas, leoninas, riscos juridicos, pontos de atencao "
        "e recomendacoes. Seja objetivo e profissional.\n\n"
        f"Contrato ({total_tokens} palavras):\n{texto}"
        f"{info_clausulas}\n\n"
        "Produza a analise conclusiva em portugues, com secoes claras."
    )

    resposta = gerar_resumo_gemini(prompt, tipo="analise conclusiva", modelo=MODEL_ANALISE)

    if resposta and "indisponivel" not in resposta.lower() and "nao foi possivel" not in resposta.lower():
        return resposta

    # Fallback local se a IA estiver indisponivel
    if clausulas:
        return (
            " **Análise Crítica:**\n"
            "O documento apresenta indícios de cláusulas que podem ser consideradas **abusivas ou leoninas**. "
            "É recomendada uma análise jurídica especializada. \n\n"
            "Cláusulas suspeitas detectadas:\n" + "\n".join(f"- {c}" for c in clausulas) +
            f"\n\n O documento contém aproximadamente {total_tokens} palavras relevantes."
        )
    return (
        " **Análise Crítica:**\n"
        "Não foram detectadas cláusulas explicitamente abusivas, mas é recomendada uma leitura completa por um especialista. "
        f"O documento contém aproximadamente {total_tokens} palavras relevantes."
    )
