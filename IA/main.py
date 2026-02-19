import logging
import json
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Optional
import spacy
from fastapi.middleware.cors import CORSMiddleware

# Serviços e dados
from data.loader import carregar_artigos, carregar_situacoes, carregar_contratos
from services.resumo_video import gerar_resumo_video
from services.resumo_pdf import gerar_resumo_pdf
from services.groq_client import gerar_resposta_groq  


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


app = FastAPI(title="Assistente Jurídico API", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


try:
    nlp = spacy.load("pt_core_news_sm")
except OSError:
    import spacy.cli
    spacy.cli.download("pt_core_news_sm")
    nlp = spacy.load("pt_core_news_sm")


try:
    dados_juridicos = carregar_artigos()
    dados_situacoes = carregar_situacoes()
    dados_contratos = carregar_contratos()
    logging.info("Todos os dados foram carregados com sucesso.")
except Exception as e:
    logging.error(f"Erro ao carregar arquivos de dados: {e}")
    raise RuntimeError(f"Erro ao carregar arquivos de dados: {e}")


class Pergunta(BaseModel):
    texto: str
    tipo: Optional[str] = "consulta"

class VideoReq(BaseModel):
    link: str
    tipo: Optional[str] = "consulta"


def _normalizar_tipo(tipo: Optional[str]) -> str:
    t = (tipo or "consulta").strip().lower()
    if t in {"consulta"}:
        return "consulta"
    if t in {"situacao", "analise_situacao"}:
        return "analise_situacao"
    if t in {"contrato", "analise_contrato"}:
        return "analise_contrato"
    return "consulta"

def analisar_pergunta_spacy(pergunta: str, dados: List[Dict]) -> List[Dict]:
    """Analisa a pergunta e retorna itens relevantes da base usando spaCy"""
    doc = nlp(pergunta)
    lemas_pergunta = {token.lemma_.lower() for token in doc if not token.is_stop and not token.is_punct}

    resultados = []
    for item in dados:
        texto_base = ""
        if 'artigo' in item:
            texto_base = f"{item.get('artigo','')} {item.get('tema','')} {item.get('texto','')} {item.get('explicacao','')}"
        elif 'descricao' in item:
            texto_base = f"{item.get('descricao','')} {item.get('analise','')}"
        elif 'tipo' in item:
            texto_base = f"{item.get('tipo','')} {item.get('analise','')}"
        else:
            texto_base = json.dumps(item, ensure_ascii=False)

        doc_base = nlp(texto_base)
        lemas_base = {token.lemma_.lower() for token in doc_base if not token.is_stop and not token.is_punct}
        interseccao = lemas_pergunta & lemas_base

        if interseccao:
            resultados.append({"item": item, "palavras_em_comum": list(interseccao)})

    return resultados

def formatar_resposta_natural(resultados: List[Dict]) -> str:
    """Formata resultados em resposta humanizada"""
    if not resultados:
        return "Não encontrei informações relevantes."
    respostas = []
    for resultado in resultados:
        item = resultado["item"]
        if 'artigo' in item:
            texto = (
                f" **Base Legal: {item.get('artigo','')} - {item.get('tema','')}**\n\n"
                f"{item.get('texto','')}\n\n"
                f" **Explicação:** {item.get('explicacao','')}"
            )
        elif 'descricao' in item:
            texto = (
                f" **Situação Jurídica:** {item.get('descricao','')}\n\n"
                f" **Análise:** {item.get('analise','')}"
            )
        elif 'tipo' in item:
            texto = (
                f" **Contrato:** {item.get('tipo','')}\n\n"
                f" **Análise:** {item.get('analise','')}"
            )
        else:
            texto = ":( Não foi possível formatar a resposta."
        respostas.append(texto)
    return "\n\n---\n\n".join(respostas)

def criar_contexto_para_ia(tipo: str) -> str:
    """Concatena dados relevantes para enviar ao Groq"""
    if tipo == "consulta":
        base = dados_juridicos
    elif tipo == "analise_situacao":
        base = dados_situacoes
    elif tipo == "analise_contrato":
        base = dados_contratos
    else:
        base = dados_juridicos

    resultados = analisar_pergunta_spacy("", base)  
    textos = [json.dumps(r["item"], ensure_ascii=False) for r in resultados]
    return "\n\n".join(textos)

# ENDPOINTS 
@app.post("/perguntar")
def responder_pergunta(p: Pergunta):
    texto_pergunta = (p.texto or "").strip()
    if len(texto_pergunta) < 1:
        raise HTTPException(status_code=400, detail="Pergunta vazia. Forneça algum texto.")

    tipo_norm = _normalizar_tipo(p.tipo)
    conteudo_para_ia = criar_contexto_para_ia(tipo_norm)

    
    resposta_ia = gerar_resposta_groq(f"{texto_pergunta}\n\nContexto relevante:\n{conteudo_para_ia}")
    return {"resposta": resposta_ia}

@app.post("/resumir_video")
def resumir_video(req: VideoReq):
    resumo = gerar_resumo_video(req.link)
    if resumo.startswith("⚠️"):
        raise HTTPException(status_code=404, detail=resumo)
    return {"resumo": resumo}

@app.post("/resumir_pdf")
def resumir_pdf_endpoint(file: UploadFile = File(...), tipo: Optional[str] = None):
    try:
        file_bytes = file.file.read()
        resultado = gerar_resumo_pdf(file_bytes)
        if tipo:
            resultado["tipo"] = _normalizar_tipo(tipo)
        return resultado
    except Exception as e:
        logging.error(f"Erro ao resumir PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao ler ou resumir PDF: {e}")

@app.get("/health")
def health():
    return {"status": "ok"}

# MAIN 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
