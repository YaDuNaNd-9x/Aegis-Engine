
from fastapi import APIRouter

from backend.app.core.config import settings
from backend.app.llm.ollama_client import ollama_client


router = APIRouter(
    prefix="/health",
    tags=["System Health"]
)


@router.get("/")
async def health_check():

    connected = await ollama_client.check_connection()

    models = []

    if connected:
        try:
            available_models = await ollama_client.list_models()

            models = [
                model.get("name")
                for model in available_models
            ]

        except Exception:
            connected = False

    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational" if connected else "degraded",
        "ollama_connected": connected,
        "available_models": models
    }
