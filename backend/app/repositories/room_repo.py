import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.db_models import Camera, Device, Room


class RoomRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> list[Room]:
        result = await self.db.execute(
            select(Room).options(
                selectinload(Room.devices),
                selectinload(Room.cameras),
            )
        )
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Room | None:
        result = await self.db.execute(
            select(Room)
            .where(Room.name == name)
            .options(selectinload(Room.devices), selectinload(Room.cameras))
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, room_id: uuid.UUID) -> Room | None:
        result = await self.db.execute(
            select(Room)
            .where(Room.id == room_id)
            .options(selectinload(Room.devices), selectinload(Room.cameras))
        )
        return result.scalar_one_or_none()

    async def create(self, name: str, friendly_name: str | None = None) -> Room:
        room = Room(name=name, friendly_name=friendly_name)
        self.db.add(room)
        await self.db.commit()
        await self.db.refresh(room)
        return room

    async def upsert(self, name: str, friendly_name: str | None = None) -> Room:
        room = await self.get_by_name(name)
        if room:
            room.friendly_name = friendly_name
            await self.db.commit()
            await self.db.refresh(room)
            return room
        return await self.create(name, friendly_name)

    async def delete(self, room_id: uuid.UUID) -> bool:
        room = await self.get_by_id(room_id)
        if not room:
            return False
        await self.db.delete(room)
        await self.db.commit()
        return True

    async def replace_from_legacy_config(self, rooms_config: dict[str, Any]) -> list[Room]:
        """Replace rooms/devices/cameras using the old rooms.json shape."""
        existing = await self.get_all()
        for room in existing:
            await self.db.delete(room)
        await self.db.flush()

        created: list[Room] = []
        for name, config in rooms_config.items():
            if not isinstance(config, dict):
                config = {}
            room = Room(
                name=str(name).strip().lower(),
                friendly_name=config.get("friendly_name") or str(name),
            )
            self.db.add(room)
            await self.db.flush()

            light_entity_id = config.get("light_entity_id")
            if light_entity_id:
                self.db.add(
                    Device(
                        room_id=room.id,
                        name=config.get("light_name") or "Luz principal",
                        entity_id=light_entity_id,
                        domain=config.get("light_domain") or "light",
                        device_type="light",
                        config={},
                    )
                )

            camera_source = config.get("camera_source")
            if camera_source:
                self.db.add(
                    Camera(
                        room_id=room.id,
                        name=config.get("camera_name") or "Camera principal",
                        source_url=str(camera_source),
                        is_default=True,
                    )
                )

            created.append(room)

        await self.db.commit()
        return created

    # ── Device helpers ────────────────────────────────────────────────────

    async def add_device(
        self,
        room_id: uuid.UUID,
        name: str,
        entity_id: str,
        domain: str,
        device_type: str,
        config: dict[str, Any] | None = None,
    ) -> Device:
        device = Device(
            room_id=room_id,
            name=name,
            entity_id=entity_id,
            domain=domain,
            device_type=device_type,
            config=config,
        )
        self.db.add(device)
        await self.db.commit()
        await self.db.refresh(device)
        return device

    async def add_camera(
        self,
        room_id: uuid.UUID,
        name: str,
        source_url: str,
        username: str | None = None,
        password: str | None = None,
        is_default: bool = False,
    ) -> Camera:
        if is_default:
            await self._clear_default_cameras(room_id)
        camera = Camera(
            room_id=room_id,
            name=name,
            source_url=source_url,
            username=username,
            password=password,
            is_default=is_default,
        )
        self.db.add(camera)
        await self.db.commit()
        await self.db.refresh(camera)
        return camera

    async def _clear_default_cameras(self, room_id: uuid.UUID) -> None:
        result = await self.db.execute(select(Camera).where(Camera.room_id == room_id))
        for camera in result.scalars().all():
            camera.is_default = False

    async def get_light_entity(self, room_name: str) -> tuple[str, str] | None:
        """Return (entity_id, domain) for the light device in a room."""
        room = await self.get_by_name(room_name)
        if not room:
            return None
        for device in room.devices:
            if device.device_type == "light":
                return device.entity_id, device.domain
        return None

    async def get_default_camera(self, room_name: str) -> str | None:
        """Return source_url of the default camera for a room."""
        room = await self.get_by_name(room_name)
        if not room:
            return None
        for cam in room.cameras:
            if cam.is_default:
                return cam.source_url
        if room.cameras:
            return room.cameras[0].source_url
        return None

    async def get_global_default_camera(self) -> str | None:
        """Return the first default camera, falling back to any registered camera."""
        result = await self.db.execute(select(Camera).where(Camera.is_default.is_(True)))
        camera = result.scalars().first()
        if camera:
            return camera.source_url

        result = await self.db.execute(select(Camera))
        camera = result.scalars().first()
        return camera.source_url if camera else None

    async def get_camera_by_name(self, name: str) -> Camera | None:
        """Case-insensitive search for a camera by name across all rooms."""
        from sqlalchemy import func as sqlfunc
        result = await self.db.execute(
            select(Camera).where(sqlfunc.lower(Camera.name) == name.strip().lower())
        )
        return result.scalar_one_or_none()
