from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import (
    ConfigEntry,
    ConfigUpdateRequest,
    OkResponse,
    RoomsConfigResponse,
    RoomsConfigUpdateRequest,
)
from app.repositories.config_repo import ConfigRepository
from app.repositories.room_repo import RoomRepository

router = APIRouter(prefix="/config", tags=["config"])


@router.get("", response_model=list[ConfigEntry])
async def get_all_config(db: AsyncSession = Depends(get_db)):
    repo = ConfigRepository(db)
    rows = await repo.get_all()
    return [ConfigEntry(key=r.key, value=r.value, description=r.description) for r in rows]


@router.get("/rooms", response_model=RoomsConfigResponse)
async def get_rooms_config(db: AsyncSession = Depends(get_db)):
    """Compatibility view that exposes rooms in the old rooms.json shape."""
    repo = RoomRepository(db)
    rooms = await repo.get_all()
    payload = {}
    for room in rooms:
        light = next((device for device in room.devices if device.device_type == "light"), None)
        camera = next((cam for cam in room.cameras if cam.is_default), None) or (room.cameras[0] if room.cameras else None)
        payload[room.name] = {
            "friendly_name": room.friendly_name,
            "light_entity_id": light.entity_id if light else "",
            "light_domain": light.domain if light else "light",
            "camera_source": camera.source_url if camera else "",
        }
    return RoomsConfigResponse(rooms=payload)


@router.post("/rooms", response_model=OkResponse)
async def update_rooms_config(
    payload: RoomsConfigUpdateRequest, db: AsyncSession = Depends(get_db)
):
    """Compatibility update that imports the old rooms.json shape into PostgreSQL."""
    repo = RoomRepository(db)
    await repo.replace_from_legacy_config(payload.rooms)
    return OkResponse(ok=True, message="Configuracao de comodos salva no banco.")


@router.get("/{key}")
async def get_config(key: str, db: AsyncSession = Depends(get_db)):
    repo = ConfigRepository(db)
    value = await repo.get(key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Chave '{key}' não encontrada.")
    return {"key": key, "value": value}


@router.put("/{key}", response_model=ConfigEntry)
async def set_config(
    key: str, payload: ConfigUpdateRequest, db: AsyncSession = Depends(get_db)
):
    repo = ConfigRepository(db)
    row = await repo.set(key, payload.value, payload.description)
    return ConfigEntry(key=row.key, value=row.value, description=row.description)


@router.delete("/{key}", response_model=OkResponse)
async def delete_config(key: str, db: AsyncSession = Depends(get_db)):
    repo = ConfigRepository(db)
    ok = await repo.delete(key)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Chave '{key}' não encontrada.")
    return OkResponse(ok=True, message=f"Chave '{key}' removida.")
