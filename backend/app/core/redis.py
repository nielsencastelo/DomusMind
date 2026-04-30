import json
from typing import Any

import redis.asyncio as aioredis

from app.core.settings import settings

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


# ── Session helpers ────────────────────────────────────────────────────────────

async def session_get(session_id: str) -> list[dict]:
    r = await get_redis()
    raw = await r.get(f"session:{session_id}")
    if not raw:
        return []
    return json.loads(raw)


async def session_append(session_id: str, role: str, content: str) -> None:
    r = await get_redis()
    key = f"session:{session_id}"
    history: list[dict] = []
    raw = await r.get(key)
    if raw:
        history = json.loads(raw)
    history.append({"role": role, "content": content})
    # keep last 20 messages only
    history = history[-20:]
    await r.setex(key, settings.redis_session_ttl, json.dumps(history))


async def session_clear(session_id: str) -> None:
    r = await get_redis()
    await r.delete(f"session:{session_id}")


# ── Generic cache helpers ──────────────────────────────────────────────────────

async def cache_set(key: str, value: Any, ttl: int = 60) -> None:
    r = await get_redis()
    await r.setex(key, ttl, json.dumps(value))


async def cache_get(key: str) -> Any | None:
    r = await get_redis()
    raw = await r.get(key)
    return json.loads(raw) if raw else None
