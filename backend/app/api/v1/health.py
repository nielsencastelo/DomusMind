from fastapi import APIRouter
from pydantic import BaseModel

from app.core.version import APP_VERSION
from app.models.schemas import HealthResponse, ServiceStatus
from app.services.ha_service import HAService

router = APIRouter(prefix="/health", tags=["health"])


class VersionResponse(BaseModel):
    version: str
    name: str = "DomusMind"


@router.get("/version", response_model=VersionResponse, tags=["version"])
async def get_version():
    return VersionResponse(version=APP_VERSION)


@router.get("", response_model=HealthResponse)
async def health():
    services: list[ServiceStatus] = []

    # Home Assistant
    ha = HAService()
    ha_result = await ha.ping()
    services.append(ServiceStatus(
        name="home_assistant",
        ok=ha_result["ok"],
        message=ha_result["message"],
    ))

    # Redis
    try:
        from app.core.redis import get_redis
        r = await get_redis()
        await r.ping()
        services.append(ServiceStatus(name="redis", ok=True, message="Redis acessível"))
    except Exception as exc:
        services.append(ServiceStatus(name="redis", ok=False, message=str(exc)))

    # PostgreSQL
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        services.append(ServiceStatus(name="postgres", ok=True, message="PostgreSQL acessível"))
    except Exception as exc:
        services.append(ServiceStatus(name="postgres", ok=False, message=str(exc)))

    # Compute device
    try:
        from app.core.compute import cpu_name, cuda_status

        gpu = cuda_status()
        if gpu["available"]:
            services.append(ServiceStatus(
                name="compute",
                ok=True,
                message=f"GPU: {gpu['device_name']} ({gpu['device_count']} CUDA)",
            ))
        else:
            services.append(ServiceStatus(
                name="compute",
                ok=True,
                message=f"CPU: {cpu_name()}",
            ))
    except Exception as exc:
        services.append(ServiceStatus(name="compute", ok=True, message=f"CPU: {exc}"))

    overall = "ok" if all(s.ok for s in services) else "degraded"
    return HealthResponse(status=overall, services=services)
