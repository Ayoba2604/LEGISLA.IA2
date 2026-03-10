from fastapi import APIRouter

from backend.app.api.routes.admin import router as admin_router
from backend.app.api.routes.chat import router as chat_router
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.ingestion import router as ingestion_router

router = APIRouter()
router.include_router(health_router)
router.include_router(admin_router)
router.include_router(chat_router)
router.include_router(ingestion_router)
