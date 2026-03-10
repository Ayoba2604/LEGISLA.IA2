from __future__ import annotations

from fastapi import HTTPException, UploadFile, status

from backend.app.config.settings import settings


async def validate_upload(file: UploadFile) -> bytes:
    if file.content_type not in settings.allowed_upload_mime_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipo de arquivo não permitido: {file.content_type}",
        )

    payload = await file.read()
    if len(payload) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo excede o limite de {settings.max_upload_bytes} bytes.",
        )
    return payload

