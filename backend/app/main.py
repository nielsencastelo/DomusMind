from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.redis import close_redis, get_redis
from app.core.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: warm up Redis connection
    await get_redis()
    yield
    # Shutdown: close Redis gracefully
    await close_redis()


def create_app() -> FastAPI:
    app = FastAPI(
        title="DomusMind API",
        version="2.0.0",
        description="Backend do assistente doméstico inteligente DomusMind",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    return app


app = create_app()
