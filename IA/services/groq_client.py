import logging
from groq import Groq


GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)

logging.basicConfig(level=logging.INFO)

def gerar_resposta_groq(pergunta: str, base_dados: list = None) -> str:
    """
    Pergunta a IA jurídica. Se base_dados for fornecida, ela é incluída no prompt.
    """
    contexto = ""
    if base_dados:
        for item in base_dados:
            if 'artigo' in item:
                contexto += f"Artigo: {item['artigo']}\nTema: {item.get('tema','')}\nTexto: {item.get('texto','')}\nExplicação: {item.get('explicacao','')}\n\n"
            elif 'descricao' in item:
                contexto += f"Situação: {item['descricao']}\nAnálise: {item.get('analise','')}\n\n"
            elif 'tipo' in item:
                contexto += f"Contrato: {item['tipo']}\nAnálise: {item.get('analise','')}\n\n"

    prompt = f"""
Você é uma assistente jurídica virtual. Use o contexto abaixo para responder à pergunta.
Contexto:
{contexto}

Pergunta do usuário: {pergunta}
Responda de forma clara, objetiva e educada.
"""
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant"
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f":(  Erro ao gerar resposta: {e}"


def gerar_resumo_groq(texto: str, tipo: str = "resumo") -> str:
    """
    Gera um resumo ou resposta de forma estruturada usando LLaMA-3.1-8b-instant.
    - texto: conteúdo a ser resumido ou interpretado
    - tipo: tipo de resumo, por exemplo 'resumo de documento jurídico'
    """
    prompt = f"""
Você é uma IA jurídica experiente. Sua tarefa é analisar o seguinte conteúdo
e produzir um resumo ou resposta clara e estruturada em português, de acordo
com o tipo solicitado: {tipo.upper()}.

Conteúdo:
{texto}
"""

    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-120b",
            temperature=0.2, 
        )
        
        msg = getattr(response.choices[0].message, "content", "")
        return msg.strip() if msg else "⚠️ Não foi possível gerar a resposta."
    except Exception as e:
        logging.error(f"Erro no Groq: {e}", exc_info=True)
        return f"⚠️ Erro ao gerar resposta com Groq: {e}"

def gerar_resposta_generica_groq(texto: str) -> str:
    """
    Função genérica para pedir à IA que se apresente ou responda perguntas jurídicas.
    """
    return gerar_resumo_groq(texto, tipo="resposta teste")
