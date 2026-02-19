import re
import spacy

try:
    nlp = spacy.load("pt_core_news_sm")
except OSError:
    import spacy.cli
    spacy.cli.download("pt_core_news_sm")
    nlp = spacy.load("pt_core_news_sm")


def detectar_clausulas_abusivas(texto: str) -> list:
    """
    Identifica possíveis cláusulas leoninas ou abusivas no texto.
    """
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
    """
    Gera uma conclusão crítica e humanizada sobre o contrato.
    """
    clausulas = detectar_clausulas_abusivas(texto)
    doc = nlp(texto)
    total_tokens = len([t for t in doc if not t.is_punct])

    if clausulas:
        conclusao = (
            " **Análise Crítica:**\n"
            "O documento apresenta indícios de cláusulas que podem ser consideradas **abusivas ou leoninas**. "
            "É recomendada uma análise jurídica especializada. \n\n"
            "Cláusulas suspeitas detectadas:\n" + "\n".join(f"- {c}" for c in clausulas) +
            f"\n\n🔎 O documento contém aproximadamente {total_tokens} palavras relevantes."
        )
    else:
        conclusao = (
            " **Análise Crítica:**\n"
            "Não foram detectadas cláusulas explicitamente abusivas, mas é recomendada uma leitura completa por um especialista. "
            f"O documento contém aproximadamente {total_tokens} palavras relevantes."
        )

    return conclusao
