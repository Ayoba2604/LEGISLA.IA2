from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile

from backend.app.config.settings import settings
from backend.app.core.enums import ResponseMode
from backend.app.schemas.chat import ChatRequest
from backend.app.security.auth import get_optional_authenticated_user, require_authenticated_user
from backend.app.security.tokens import AuthenticatedUser
from backend.app.security.uploads import validate_upload

router = APIRouter(tags=["chat"])


def _chat_service(request: Request):
    return request.app.state.chat_service


@router.post("/perguntar")
async def legacy_perguntar(
    payload: dict,
    request: Request,
    user: AuthenticatedUser | None = Depends(get_optional_authenticated_user),
):
    text = (payload.get("texto") or "").strip()
    raw_mode = payload.get("modo") or payload.get("mode") or "friendly"
    if not text:
        raise HTTPException(status_code=400, detail="Pergunta vazia.")
    try:
        mode = ResponseMode(raw_mode)
    except ValueError:
        mode = ResponseMode.FRIENDLY
    chat_request = ChatRequest(question=text, mode=mode, debug=bool(payload.get("debug")))
    return _chat_service(request).answer(chat_request, authenticated_user=user).model_dump()


@router.get("/consulta")
def legacy_consulta(
    request: Request,
    artigo: str | None = None,
    tema: str | None = None,
    user: AuthenticatedUser | None = Depends(get_optional_authenticated_user),
):
    query = artigo or tema
    if not query:
        raise HTTPException(status_code=400, detail="Informe artigo ou tema.")
    chat_request = ChatRequest(question=query, mode=ResponseMode.TECHNICAL)
    return _chat_service(request).answer(chat_request, authenticated_user=user).model_dump()


@router.post("/resumir_pdf")
async def resumir_pdf_endpoint(
    request: Request,
    file: UploadFile,
    user: AuthenticatedUser = Depends(require_authenticated_user),
):
    payload = await validate_upload(file)
    source, chunks, warnings, injection_detected = request.app.state.ingestion_pipeline.ingest_upload(
        filename=file.filename or "documento.pdf",
        mime_type=file.content_type or "application/pdf",
        payload=payload,
        metadata={
            "owner_user_id": user.user_id,
            "owner_email": user.email,
            "retention_expires_at": (
                datetime.utcnow() + timedelta(days=settings.user_upload_retention_days)
            ).isoformat(),
        },
    )
    request.app.state.catalog.add_source(source, chunks)
    if getattr(request.app.state, "persistence", None):
        request.app.state.persistence.record_upload(
            conversation_id=None,
            filename=file.filename or "documento.pdf",
            mime_type=file.content_type or "application/pdf",
            file_size=len(payload),
            source_id=source.source_id,
            owner_user_id=user.user_id,
            retention_expires_at=datetime.utcnow() + timedelta(days=settings.user_upload_retention_days),
        )
    summary = request.app.state.chat_service.summarize_text(source.raw_text, mode="resumo de documento juridico")
    return {"resumo": summary, "warnings": warnings, "prompt_injection": injection_detected}


@router.post("/resumir_video")
async def resumir_video_endpoint(payload: dict, request: Request):
    link = payload.get("link", "")
    return {"resumo": f"Resumo de video indisponivel no modo offline. Link recebido: {link}"}


@router.post("/api/v1/chat/query")
def chat_query(
    chat_request: ChatRequest,
    request: Request,
    user: AuthenticatedUser | None = Depends(get_optional_authenticated_user),
):
    if chat_request.user_document_ids and user is None:
        raise HTTPException(status_code=401, detail="Autenticacao obrigatoria para consultar documentos do usuario.")
    return _chat_service(request).answer(chat_request, authenticated_user=user).model_dump()
