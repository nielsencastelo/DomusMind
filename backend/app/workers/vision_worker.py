import asyncio

from app.celery import celery_app
from app.core.settings import settings
from app.services.vision_service import VisionService


@celery_app.task(name="app.workers.vision_worker.monitor_default_camera")
def monitor_default_camera() -> dict[str, str]:
    return asyncio.run(_monitor_default_camera())


async def _monitor_default_camera() -> dict[str, str]:
    vision = VisionService()
    description = await vision.describe(settings.default_camera_source, use_gemini=False)
    status = "person_detected" if "person" in description.lower() or "pessoa" in description.lower() else "ok"
    return {"status": status, "description": description}
