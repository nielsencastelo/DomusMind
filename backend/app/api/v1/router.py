from fastapi import APIRouter

from app.api.v1.chat import router as chat_router
from app.api.v1.config import router as config_router
from app.api.v1.devices import router as devices_router
from app.api.v1.health import router as health_router
from app.api.v1.memory import router as memory_router
from app.api.v1.vision import router as vision_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(chat_router)
api_router.include_router(vision_router)
api_router.include_router(devices_router)
api_router.include_router(memory_router)
api_router.include_router(config_router)
api_router.include_router(health_router)
