import asyncio
import json

from app.celery import celery_app
from app.core.redis import get_redis
from app.services.ha_service import HAService


@celery_app.task(name="app.workers.ha_sync_worker.sync_ha_states")
def sync_ha_states() -> dict[str, int | str]:
    return asyncio.run(_sync_ha_states())


async def _sync_ha_states() -> dict[str, int | str]:
    ha = HAService()
    states = await ha.get_all_states()
    redis = await get_redis()

    count = 0
    for state in states:
        entity_id = state.get("entity_id")
        if not entity_id:
            continue
        await redis.setex(f"ha_state:{entity_id}", 10, json.dumps(state))
        count += 1

    return {"status": "ok", "synced": count}
