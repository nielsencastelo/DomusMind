from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import ConfigEntry, ConfigUpdateRequest, OkResponse
from app.repositories.config_repo import ConfigRepository

router = APIRouter(prefix="/config", tags=["config"])


@router.get("", response_model=list[ConfigEntry])
async def get_all_config(db: AsyncSession = Depends(get_db)):
    repo = ConfigRepository(db)
    rows = await repo.get_all()
    return [ConfigEntry(key=r.key, value=r.value, description=r.description) for r in rows]


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
