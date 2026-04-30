from fastapi import APIRouter

from app.models.schemas import HealthResponse, ServiceStatus
from app.services.ha_service import HAService

router = APIRouter(prefix="/health", tags=["health"])


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

    # GPU / CUDA
    try:
        from app.core.compute import cuda_status

        gpu = cuda_status()
        if gpu["available"]:
            services.append(ServiceStatus(
                name="gpu",
                ok=True,
                message=f"CUDA disponivel: {gpu['device_name']} ({gpu['device_count']} GPU)",
            ))
        else:
            services.append(ServiceStatus(
                name="gpu",
                ok=False,
                message="CUDA indisponivel no container; modelos vao usar CPU.",
            ))
    except Exception as exc:
        services.append(ServiceStatus(name="gpu", ok=False, message=str(exc)))

    overall = "ok" if all(s.ok for s in services) else "degraded"
    return HealthResponse(status=overall, services=services)
