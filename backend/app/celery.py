from celery import Celery

from app.core.settings import settings


celery_app = Celery(
    "domusmind",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.ha_sync_worker",
        "app.workers.memory_consolidation_worker",
        "app.workers.vision_worker",
    ],
)

celery_app.conf.update(
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_default_queue="default",
    beat_schedule={
        "sync-ha-states-every-30-seconds": {
            "task": "app.workers.ha_sync_worker.sync_ha_states",
            "schedule": 30.0,
            "options": {"queue": "ha"},
        },
        "consolidate-memory-hourly": {
            "task": "app.workers.memory_consolidation_worker.consolidate_recent_conversations",
            "schedule": 3600.0,
            "options": {"queue": "memory"},
        },
        "monitor-default-camera": {
            "task": "app.workers.vision_worker.monitor_default_camera",
            "schedule": settings.vision_monitor_interval_seconds,
            "options": {"queue": "vision"},
        },
    },
)

app = celery_app

__all__ = ["app", "celery_app"]
