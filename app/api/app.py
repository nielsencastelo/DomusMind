from fastapi import FastAPI

from app.api.routes.chat import router as chat_router
from app.api.routes.config import router as config_router
from app.api.routes.devices import router as devices_router
from app.api.routes.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="DomusMind API",
        version="2.0.0",
        description="API do assistente residencial DomusMind",
    )

    app.include_router(chat_router, prefix="/api/v1", tags=["chat"])
    app.include_router(config_router, prefix="/api/v1", tags=["config"])
    app.include_router(devices_router, prefix="/api/v1", tags=["devices"])
    app.include_router(health_router, prefix="/api/v1", tags=["health"])

    return app


app = create_app()