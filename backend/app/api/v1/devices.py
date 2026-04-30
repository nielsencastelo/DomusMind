import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.models.schemas import (
    CameraIn,
    CameraOut,
    DeviceActionResponse,
    DeviceIn,
    DeviceOut,
    LightActionRequest,
    OkResponse,
    RoomIn,
    RoomOut,
)
from app.repositories.room_repo import RoomRepository
from app.services.ha_service import HAService

router = APIRouter(prefix="/devices", tags=["devices"])


# ── Light control ──────────────────────────────────────────────────────────────

@router.post("/light", response_model=DeviceActionResponse)
async def toggle_light(payload: LightActionRequest, db: AsyncSession = Depends(get_db)):
    repo = RoomRepository(db)
    light = await repo.get_light_entity(payload.room)
    if not light:
        raise HTTPException(
            status_code=404,
            detail=f"Luz do cômodo '{payload.room}' não encontrada.",
        )
    entity_id, domain = light
    ha = HAService()
    ok, msg = await ha.toggle_light(entity_id, domain, turn_on=(payload.action == "on"))
    return DeviceActionResponse(ok=ok, message=msg)


# ── HA states ─────────────────────────────────────────────────────────────────

@router.get("/ha/states")
async def get_ha_states():
    """Return all Home Assistant entity states."""
    ha = HAService()
    return await ha.get_all_states()


@router.get("/ha/state/{entity_id:path}")
async def get_ha_state(entity_id: str):
    ha = HAService()
    state = await ha.get_state(entity_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Entidade '{entity_id}' não encontrada.")
    return state


@router.get("/ha/cache")
async def get_cached_ha_states(pattern: str = "*"):
    """Return HA states synchronized by the Celery worker into Redis."""
    redis = await get_redis()
    keys = await redis.keys(f"ha_state:{pattern}")
    states = []
    for key in keys:
        raw = await redis.get(key)
        if raw:
            states.append(json.loads(raw))
    return states


@router.get("/ha/cache/{entity_id:path}")
async def get_cached_ha_state(entity_id: str):
    redis = await get_redis()
    raw = await redis.get(f"ha_state:{entity_id}")
    if raw is None:
        raise HTTPException(status_code=404, detail=f"Estado em cache para '{entity_id}' nao encontrado.")
    return json.loads(raw)


# ── Room CRUD ─────────────────────────────────────────────────────────────────

@router.get("/rooms", response_model=list[RoomOut])
async def list_rooms(db: AsyncSession = Depends(get_db)):
    repo = RoomRepository(db)
    return await repo.get_all()


@router.post("/rooms", response_model=RoomOut, status_code=201)
async def create_room(payload: RoomIn, db: AsyncSession = Depends(get_db)):
    repo = RoomRepository(db)
    room = await repo.upsert(payload.name, payload.friendly_name)
    for d in payload.devices:
        await repo.add_device(
            room.id,
            d.name,
            d.entity_id,
            d.domain,
            d.device_type,
            d.config,
        )
    for c in payload.cameras:
        await repo.add_camera(
            room.id,
            c.name,
            c.source_url,
            c.username,
            c.password,
            c.is_default,
        )
    return await repo.get_by_id(room.id)


@router.delete("/rooms/{room_id}", response_model=OkResponse)
async def delete_room(room_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    repo = RoomRepository(db)
    ok = await repo.delete(room_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Cômodo não encontrado.")
    return OkResponse(ok=True, message="Cômodo removido.")


@router.post("/rooms/{room_id}/cameras", response_model=CameraOut, status_code=201)
async def add_camera(
    room_id: uuid.UUID, payload: CameraIn, db: AsyncSession = Depends(get_db)
):
    repo = RoomRepository(db)
    cam = await repo.add_camera(
        room_id,
        payload.name,
        payload.source_url,
        payload.username,
        payload.password,
        payload.is_default,
    )
    return cam


@router.post("/rooms/{room_id}/devices", response_model=DeviceOut, status_code=201)
async def add_device(
    room_id: uuid.UUID, payload: DeviceIn, db: AsyncSession = Depends(get_db)
):
    repo = RoomRepository(db)
    device = await repo.add_device(
        room_id,
        payload.name,
        payload.entity_id,
        payload.domain,
        payload.device_type,
        payload.config,
    )
    return device
