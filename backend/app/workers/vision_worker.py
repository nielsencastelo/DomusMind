import asyncio

from app.celery import celery_app
from app.core.settings import settings
from app.services.vision_service import VisionService


@celery_app.task(name="app.workers.vision_worker.monitor_default_camera")
def monitor_default_camera() -> dict[str, str]:
    return asyncio.run(_monitor_default_camera())


async def _monitor_default_camera() -> dict[str, str]:
    vision = VisionService()
    source = settings.default_camera_source
    try:
        from app.core.database import AsyncSessionLocal
        from app.repositories.room_repo import RoomRepository

        async with AsyncSessionLocal() as db:
            camera_source = await RoomRepository(db).get_global_default_camera()
        if camera_source:
            source = camera_source
    except Exception:
        pass

    description = await vision.describe(source, use_gemini=False)
    lowered = description.lower()
    if "yolo nao esta instalado" in lowered:
        status = "vision_unconfigured"
    elif "person" in lowered or "pessoa" in lowered:
        status = "person_detected"
    else:
        status = "ok"
    return {"status": status, "description": description}
