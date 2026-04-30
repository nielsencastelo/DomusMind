from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.settings import settings
from app.models.schemas import VisionRequest, VisionResponse

router = APIRouter(prefix="/vision", tags=["vision"])


@router.post("/describe", response_model=VisionResponse)
async def describe_scene(payload: VisionRequest):
    """Describe the current scene using Gemini Vision or YOLO."""
    from app.services.vision_service import VisionService
    from app.core.database import AsyncSessionLocal
    from app.repositories.room_repo import RoomRepository

    svc = VisionService()
    source = None

    if payload.room:
        try:
            async with AsyncSessionLocal() as db:
                repo = RoomRepository(db)
                source = await repo.get_default_camera(payload.room)
        except Exception:
            pass

    if source is None:
        source = settings.default_camera_source

    try:
        description = await svc.describe(source)
        return VisionResponse(ok=True, room=payload.room, description=description)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/stream/{room}")
async def stream_camera(room: str):
    """
    MJPEG live stream for a specific room's camera.
    Frontend can use: <img src="/api/v1/vision/stream/sala">
    """
    from app.services.vision_service import VisionService
    from app.core.database import AsyncSessionLocal
    from app.repositories.room_repo import RoomRepository

    svc = VisionService()
    source = settings.default_camera_source

    try:
        async with AsyncSessionLocal() as db:
            repo = RoomRepository(db)
            cam_source = await repo.get_default_camera(room)
            if cam_source:
                source = cam_source
    except Exception:
        pass

    return StreamingResponse(
        svc.mjpeg_frames(source),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/stream/default")
async def stream_default_camera():
    """MJPEG stream for the default camera source."""
    from app.services.vision_service import VisionService

    svc = VisionService()
    return StreamingResponse(
        svc.mjpeg_frames(settings.default_camera_source),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
