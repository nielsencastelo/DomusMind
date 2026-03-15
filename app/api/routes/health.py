from fastapi import APIRouter

from app.adapters.home_assistant_client import HomeAssistantClient
from app.core.settings import settings

router = APIRouter()
ha_client = HomeAssistantClient()


@router.get("/health")
def health():
    ha_status = ha_client.ping()

    return {
        "ok": True,
        "service": "DomusMind API",
        "version": "2.0.0",
        "local_model": settings.local_model,
        "ha": ha_status,
    }