from fastapi import APIRouter, HTTPException

from app.adapters.home_assistant_client import HomeAssistantClient
from app.models.schemas import (
    DeviceActionResponse,
    LightActionRequest,
    VisionRequest,
    VisionResponse,
)
from app.repositories.config_repository import ConfigRepository
from app.services.vision_service import VisionService

router = APIRouter()

ha_client = HomeAssistantClient()
vision_service = VisionService()
config_repo = ConfigRepository()


@router.post("/devices/light", response_model=DeviceActionResponse)
def control_light(payload: LightActionRequest):
    try:
        ok, message = ha_client.toggle_light(
            room=payload.room,
            turn_on=(payload.action == "on"),
        )
        return DeviceActionResponse(ok=ok, message=message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/devices/vision", response_model=VisionResponse)
def describe_camera(payload: VisionRequest):
    try:
        rooms = config_repo.load_rooms()
        room_cfg = rooms.get(payload.room, {})
        camera_source = room_cfg.get("camera_source")

        description = vision_service.capture_and_describe(camera_source=camera_source)
        return VisionResponse(
            ok=True,
            room=payload.room,
            description=description,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc