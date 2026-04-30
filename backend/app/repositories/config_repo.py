from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import SystemConfig


class ConfigRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, key: str) -> Any | None:
        result = await self.db.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        row = result.scalar_one_or_none()
        return row.value if row else None

    async def set(
        self, key: str, value: Any, description: str | None = None
    ) -> SystemConfig:
        result = await self.db.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        row = result.scalar_one_or_none()
        if row:
            row.value = value
            if description is not None:
                row.description = description
        else:
            row = SystemConfig(key=key, value=value, description=description)
            self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def get_all(self) -> list[SystemConfig]:
        result = await self.db.execute(select(SystemConfig))
        return list(result.scalars().all())

    async def delete(self, key: str) -> bool:
        result = await self.db.execute(
            select(SystemConfig).where(SystemConfig.key == key)
        )
        row = result.scalar_one_or_none()
        if not row:
            return False
        await self.db.delete(row)
        await self.db.commit()
        return True
