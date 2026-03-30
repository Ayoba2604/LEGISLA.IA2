import json
import logging
import os
import re
from typing import Dict, List, Optional

import spacy
from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api.routes import router as consulta_router
from data.loader import carregar_artigos, carregar_contratos, carregar_situacoes
from env_loader import load_project_env
from services.gemini_client import gerar_resposta_gemini
from services.resumo_pdf import gerar_resumo_pdf
from services.resumo_video import gerar_resumo_video

from app.api.router import api_router


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
load_project_env()


def _carregar_modelo_nlp():
    try:
        return spacy.load("pt_core_news_sm")
    except OSError:
        logger.warning("Modelo pt_core_news_sm nao encontrado; usando tokenizacao basica.")
        return spacy.blank("pt")


app = FastAPI(title="Assistente Juridico API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(consulta_router)
app.include_router(api_router)

nlp = _carregar_modelo_nlp()

try:
    dados_juridicos = carregar_artigos()
    dados_situacoes = carregar_situacoes()
    dados_contratos = carregar_contratos()
    logger.info("Dados carregados com sucesso.")
except Exception as exc:
    logger.error("Erro ao carregar arquivos de dados: %s", exc, exc_info=True)
    dados_juridicos = []
    dados_situacoes = []
    dados_contratos = []


class Pergunta(BaseModel):
    texto: str
    tipo: Optional[str] = "consulta"


class VideoReq(BaseModel):
    link: str
    tipo: Optional[str] = "consulta"


def _normalizar_tipo(tipo: Optional[str]) -> str:
    valor = (tipo or "consulta").strip().lower()
    if valor in {"consulta"}:
        return "consulta"
    if valor in {"situacao", "analise_situacao"}:
        return "analise_situacao"
    if valor in {"contrato", "analise_contrato"}:
        return "analise_contrato"
    return "consulta"


def _obter_base_por_tipo(tipo: str) -> List[Dict]:
    if tipo == "analise_situacao":
        return dados_situacoes
    if tipo == "analise_contrato":
        return dados_contratos
    return dados_juridicos


def _extrair_termos(texto: str) -> set[str]:
    termos = set()
    doc = nlp(texto or "")
    for token in doc:
        base = (token.lemma_ or token.text or "").strip().lower()
        base = re.sub(r"[^\w]+", "", base, flags=re.UNICODE)
        if not base or len(base) < 3 or token.is_stop or token.is_punct or token.is_space:
            continue
        termos.add(base)

    if termos:
        return termos

    return {termo for termo in re.findall(r"\w+", (texto or "").lower()) if len(termo) >= 3}


def _texto_item(item: Dict) -> str:
    campos = (
        "artigo",
        "tema",
        "titulo",
        "descricao",
        "texto",
        "explicacao",
        "analise",
        "original",
        "tipo",
        "categoria",
    )
    return " ".join(str(item.get(campo, "")).strip() for campo in campos if item.get(campo))


def analisar_pergunta_spacy(pergunta: str, dados: List[Dict]) -> List[Dict]:
    termos_pergunta = _extrair_termos(pergunta)
    if not termos_pergunta:
        return []

    resultados = []
    for item in dados:
        termos_item = _extrair_termos(_texto_item(item))
        interseccao = termos_pergunta & termos_item
        if interseccao:
            resultados.append(
                {
                    "item": item,
                    "score": len(interseccao),
                    "palavras_em_comum": sorted(interseccao),
                }
            )

    resultados.sort(key=lambda resultado: resultado["score"], reverse=True)
    return resultados[:5]


def formatar_resposta_natural(resultados: List[Dict]) -> str:
    if not resultados:
        return "Nao encontrei informacoes relevantes na base local."

    respostas = []
    for resultado in resultados:
        item = resultado["item"]
        titulo = item.get("titulo") or item.get("tema") or item.get("artigo") or "Referencia"
        descricao = item.get("descricao") or item.get("texto") or item.get("original") or ""
        analise = item.get("analise") or item.get("explicacao") or ""
        categoria = item.get("categoria") or item.get("tipo") or "consulta"

        partes = [f"Categoria: {categoria}", f"Titulo: {titulo}"]
        if descricao:
            partes.append(f"Resumo: {descricao}")
        if analise:
            partes.append(f"Analise: {analise}")

        respostas.append("\n".join(partes))

    return "\n\n---\n\n".join(respostas)


MIN_SCORE = 2


def criar_contexto_para_ia(pergunta: str, tipo: str) -> tuple[str, List[Dict]]:
    base = _obter_base_por_tipo(tipo)
    resultados = analisar_pergunta_spacy(pergunta, base)

    relevantes = [r for r in resultados if r["score"] >= MIN_SCORE]

    if not relevantes:
        return "", resultados

    textos = [json.dumps(r["item"], ensure_ascii=False) for r in relevantes[:3]]
    return "\n\n".join(textos), resultados


def _responder_pergunta(p: Pergunta) -> Dict[str, str]:
    texto_pergunta = (p.texto or "").strip()
    if not texto_pergunta:
        raise HTTPException(status_code=400, detail="Pergunta vazia. Forneca algum texto.")

    tipo_norm = _normalizar_tipo(p.tipo)
    contexto, resultados = criar_contexto_para_ia(texto_pergunta, tipo_norm)

    resposta_ia = gerar_resposta_gemini(texto_pergunta, base_dados=[contexto] if contexto else None)
    if not resposta_ia:
        resposta_ia = formatar_resposta_natural(resultados)

    return {"resposta": resposta_ia, "tipo": tipo_norm}


@app.options("/perguntar")
@app.options("/api/v1/chat/query")
def chat_preflight() -> Response:
    return Response(status_code=204)


@app.post("/perguntar")
def responder_pergunta_legacy(p: Pergunta):
    return _responder_pergunta(p)


@app.post("/api/v1/chat/query")
def responder_pergunta_v1(p: Pergunta):
    return _responder_pergunta(p)


@app.post("/resumir_video")
def resumir_video(req: VideoReq):
    resumo = gerar_resumo_video(req.link)
    if resumo.startswith("Nao foi possivel"):
        raise HTTPException(status_code=404, detail=resumo)
    return {"resumo": resumo}


@app.post("/resumir_pdf")
def resumir_pdf_endpoint(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
    tipo: Optional[str] = Form(None),
):
    try:
        file_bytes = file.file.read()
        resultado = gerar_resumo_pdf(file_bytes, prompt=prompt or "")
    except Exception as exc:
        logger.error("Erro ao resumir PDF: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao ler ou resumir PDF: {exc}") from exc

    if resultado.get("erro"):
        raise HTTPException(status_code=400, detail=resultado["erro"])

    if tipo:
        resultado["tipo"] = _normalizar_tipo(tipo)
    return resultado


@app.get("/health")
def health():
    return {"status": "ok", "fontes": len(dados_juridicos) + len(dados_situacoes) + len(dados_contratos)}


# ---------------------------------------------------------------------------
# Serve React SPA build in production
# ---------------------------------------------------------------------------
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if _FRONTEND_DIST.is_dir():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIST / "assets"), name="react-assets")
    if (_FRONTEND_DIST / "imagens").is_dir():
        app.mount("/imagens", StaticFiles(directory=_FRONTEND_DIST / "imagens"), name="imagens")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        file_path = _FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_FRONTEND_DIST / "index.html")


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("FASTAPI_HOST", "127.0.0.1")
    port = int(os.getenv("FASTAPI_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
