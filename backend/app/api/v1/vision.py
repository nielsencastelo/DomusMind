import base64
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.settings import settings
from app.models.schemas import (
    VisionRequest,
    VisionResponse,
    VisionSourceTestRequest,
    VisionSourceTestResponse,
)

router = APIRouter(prefix="/vision", tags=["vision"])


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _global_camera_source(db: AsyncSession) -> str:
    from app.repositories.room_repo import RoomRepository
    try:
        src = await RoomRepository(db).get_global_default_camera()
        if src:
            return src
    except Exception:
        pass
    return settings.default_camera_source


# ── Vision Config ──────────────────────────────────────────────────────────────

class VisionConfigOut(BaseModel):
    provider: str
    gemini_key_set: bool
    ollama_base_url: str
    ollama_model: str
    yolo_weights: str
    yolo_confidence: float
    yolo_frames: int


class VisionConfigIn(BaseModel):
    provider: str  # "yolo" | "gemini" | "ollama"
    gemini_api_key: str | None = None
    ollama_base_url: str | None = None
    ollama_model: str | None = None
    yolo_weights: str | None = None
    yolo_confidence: float | None = None
    yolo_frames: int | None = None


class YoloModelInfo(BaseModel):
    name: str
    path: str
    installed: bool
    size_bytes: int | None = None


class YoloDownloadRequest(BaseModel):
    model: str


class YoloDownloadResponse(BaseModel):
    ok: bool
    model: str
    path: str | None = None
    message: str


YOLO_MODEL_URLS = {
    "yolov8n.pt": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt",
    "yolov8s.pt": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8s.pt",
    "yolov8m.pt": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8m.pt",
    "yolov8l.pt": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8l.pt",
    "yolov8x.pt": "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8x.pt",
}


def _models_dir() -> Path:
    path = Path("/app/models")
    if not path.exists():
        path = Path("models")
    path.mkdir(parents=True, exist_ok=True)
    return path


@router.get("/config", response_model=VisionConfigOut)
async def get_vision_config(db: AsyncSession = Depends(get_db)):
    from app.repositories.config_repo import ConfigRepository
    repo = ConfigRepository(db)
    provider = await repo.get("vision.provider") or ("gemini" if settings.gemini_api_key else "yolo")
    api_key = await repo.get("vision.gemini_api_key") or ""
    ollama_base_url = await repo.get("vision.ollama_base_url")
    ollama_model = await repo.get("vision.ollama_model")
    provider_config = await repo.get("llm.providers")
    agent_config = await repo.get("llm.agents")
    local_config = provider_config.get("local", {}) if isinstance(provider_config, dict) else {}
    vision_agent = agent_config.get("visao", {}) if isinstance(agent_config, dict) else {}
    weights = await repo.get("vision.yolo_weights") or settings.yolo_weights
    confidence = await repo.get("vision.yolo_confidence")
    frames = await repo.get("vision.yolo_frames")
    return VisionConfigOut(
        provider=str(provider),
        gemini_key_set=bool(api_key),
        ollama_base_url=str(ollama_base_url or local_config.get("base_url") or settings.ollama_base_url),
        ollama_model=str(ollama_model or vision_agent.get("model") or local_config.get("default_model") or settings.local_model),
        yolo_weights=str(weights),
        yolo_confidence=float(confidence) if confidence is not None else 0.6,
        yolo_frames=int(frames) if frames is not None else 10,
    )


@router.post("/config", response_model=VisionConfigOut)
async def set_vision_config(payload: VisionConfigIn, db: AsyncSession = Depends(get_db)):
    from app.repositories.config_repo import ConfigRepository
    repo = ConfigRepository(db)

    if payload.provider not in {"yolo", "gemini", "ollama"}:
        raise HTTPException(status_code=422, detail="provider deve ser 'yolo', 'gemini' ou 'ollama'")

    await repo.set("vision.provider", payload.provider, "Provedor de visao (yolo | gemini | ollama)")

    if payload.gemini_api_key is not None:
        await repo.set("vision.gemini_api_key", payload.gemini_api_key, "API key do Gemini Vision")

    if payload.ollama_base_url is not None:
        await repo.set("vision.ollama_base_url", payload.ollama_base_url, "Base URL do Ollama Vision")

    if payload.ollama_model is not None:
        await repo.set("vision.ollama_model", payload.ollama_model, "Modelo multimodal do Ollama Vision")

    if payload.yolo_weights is not None:
        await repo.set("vision.yolo_weights", payload.yolo_weights, "Caminho dos pesos YOLO")

    if payload.yolo_confidence is not None:
        await repo.set("vision.yolo_confidence", payload.yolo_confidence, "Limiar de confiança YOLO")

    if payload.yolo_frames is not None:
        await repo.set("vision.yolo_frames", payload.yolo_frames, "Frames analisados por chamada")

    return await get_vision_config(db)


@router.get("/yolo/models", response_model=list[YoloModelInfo])
async def list_yolo_models():
    models_dir = _models_dir()
    items: list[YoloModelInfo] = []
    known = set(YOLO_MODEL_URLS)

    for name in sorted(known):
        path = models_dir / name
        items.append(
            YoloModelInfo(
                name=name,
                path=f"models/{name}",
                installed=path.exists(),
                size_bytes=path.stat().st_size if path.exists() else None,
            )
        )

    for path in sorted(models_dir.glob("*.pt")):
        if path.name in known:
            continue
        items.append(
            YoloModelInfo(
                name=path.name,
                path=f"models/{path.name}",
                installed=True,
                size_bytes=path.stat().st_size,
            )
        )

    return items


@router.post("/yolo/download", response_model=YoloDownloadResponse)
async def download_yolo_model(payload: YoloDownloadRequest, db: AsyncSession = Depends(get_db)):
    import httpx
    from app.repositories.config_repo import ConfigRepository

    model = Path(payload.model).name
    url = YOLO_MODEL_URLS.get(model)
    if not url:
        raise HTTPException(status_code=422, detail="Modelo YOLO nao suportado para download.")

    destination = _models_dir() / model
    partial = destination.with_suffix(destination.suffix + ".part")
    rel_path = f"models/{model}"

    if destination.exists():
        await ConfigRepository(db).set("vision.yolo_weights", rel_path, "Caminho dos pesos YOLO")
        return YoloDownloadResponse(ok=True, model=model, path=rel_path, message="Modelo ja instalado.")

    try:
        async with httpx.AsyncClient(timeout=None, follow_redirects=True) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                with partial.open("wb") as file:
                    async for chunk in response.aiter_bytes():
                        if chunk:
                            file.write(chunk)
        partial.replace(destination)
    except Exception as exc:
        if partial.exists():
            partial.unlink()
        return YoloDownloadResponse(ok=False, model=model, message=f"Falha ao baixar modelo: {exc}")

    await ConfigRepository(db).set("vision.yolo_weights", rel_path, "Caminho dos pesos YOLO")
    return YoloDownloadResponse(ok=True, model=model, path=rel_path, message="Modelo baixado e configurado.")


# ── Describe ───────────────────────────────────────────────────────────────────

@router.post("/describe", response_model=VisionResponse)
async def describe_scene(payload: VisionRequest, db: AsyncSession = Depends(get_db)):
    from app.services.vision_service import VisionService
    from app.repositories.room_repo import RoomRepository

    svc = VisionService()
    source = None

    if payload.room:
        try:
            source = await RoomRepository(db).get_default_camera(payload.room)
        except Exception:
            pass

    if source is None:
        source = await _global_camera_source(db)

    try:
        description = await svc.describe(source)
        return VisionResponse(ok=True, room=payload.room, description=description)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Test source (legacy, kept for compatibility) ───────────────────────────────

@router.post("/test-source", response_model=VisionSourceTestResponse)
async def test_camera_source(payload: VisionSourceTestRequest):
    from app.services.vision_service import VisionService
    svc = VisionService()
    frame = svc.capture_frame(payload.source_url)
    if frame is None:
        return VisionSourceTestResponse(
            ok=False,
            message="Nao foi possivel capturar frame da camera.",
        )
    return VisionSourceTestResponse(ok=True, message="Camera respondeu e um frame foi capturado.")


# ── Enhanced camera test (with snapshot + metadata) ───────────────────────────

class CameraTestRequest(BaseModel):
    source_url: str
    username: str | None = None
    password: str | None = None


class CameraTestResponse(BaseModel):
    ok: bool
    message: str
    latency_ms: float | None = None
    resolution: str | None = None
    fps: float | None = None
    snapshot_base64: str | None = None


@router.post("/test-camera", response_model=CameraTestResponse)
async def test_camera(payload: CameraTestRequest):
    import cv2

    source = payload.source_url.strip()
    if source.isdigit():
        cap_source: str | int = int(source)
    elif payload.username and payload.password and "://" in source:
        # Embed credentials into RTSP URL if not already present
        proto, rest = source.split("://", 1)
        if "@" not in rest:
            source = f"{proto}://{payload.username}:{payload.password}@{rest}"
        cap_source = source
    else:
        cap_source = source

    t0 = time.monotonic()
    cap = cv2.VideoCapture(cap_source)

    if not cap.isOpened():
        return CameraTestResponse(
            ok=False,
            message="Não foi possível conectar à câmera. Verifique IP, credenciais e rede.",
        )

    ret, frame = cap.read()
    latency_ms = round((time.monotonic() - t0) * 1000, 1)

    if not ret or frame is None:
        cap.release()
        return CameraTestResponse(
            ok=False,
            message="Câmera conectou mas não retornou frame. Verifique canal e configuração.",
            latency_ms=latency_ms,
        )

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = round(cap.get(cv2.CAP_PROP_FPS), 1)
    cap.release()

    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    snapshot = "data:image/jpeg;base64," + base64.b64encode(buf).decode()

    return CameraTestResponse(
        ok=True,
        message="Câmera respondeu com sucesso.",
        latency_ms=latency_ms,
        resolution=f"{w}x{h}",
        fps=fps,
        snapshot_base64=snapshot,
    )


# ── Local camera scan ──────────────────────────────────────────────────────────

class LocalCamera(BaseModel):
    index: int
    device_path: str
    resolution: str
    source_url: str


@router.get("/local-cameras", response_model=list[LocalCamera])
async def scan_local_cameras():
    import cv2

    found: list[LocalCamera] = []
    for i in range(6):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                found.append(LocalCamera(
                    index=i,
                    device_path=f"/dev/video{i}",
                    resolution=f"{w}x{h}",
                    source_url=str(i),
                ))
            cap.release()
    return found


# ── Update camera last_seen + resolution after successful test ─────────────────

async def _update_camera_meta(
    db: AsyncSession, camera_id: str, resolution: str
) -> None:
    import uuid
    from sqlalchemy import select
    from app.models.db_models import Camera

    try:
        result = await db.execute(
            select(Camera).where(Camera.id == uuid.UUID(camera_id))
        )
        cam = result.scalar_one_or_none()
        if cam:
            cam.last_seen_at = datetime.now(timezone.utc)
            cam.resolution = resolution
            await db.commit()
    except Exception:
        pass


# ── MJPEG streams ──────────────────────────────────────────────────────────────

@router.get("/stream/{room}")
async def stream_camera(room: str, db: AsyncSession = Depends(get_db)):
    from app.services.vision_service import VisionService
    from app.repositories.room_repo import RoomRepository

    svc = VisionService()
    source = await _global_camera_source(db)

    try:
        cam_source = await RoomRepository(db).get_default_camera(room)
        if cam_source:
            source = cam_source
    except Exception:
        pass

    return StreamingResponse(
        svc.mjpeg_frames(source),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/stream/camera/{camera_id}")
async def stream_camera_by_id(camera_id: str, db: AsyncSession = Depends(get_db)):
    import uuid
    from sqlalchemy import select
    from app.models.db_models import Camera
    from app.services.vision_service import VisionService

    try:
        parsed_id = uuid.UUID(camera_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="camera_id invalido.") from exc

    result = await db.execute(select(Camera).where(Camera.id == parsed_id))
    camera = result.scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera nao encontrada.")

    svc = VisionService()
    return StreamingResponse(
        svc.mjpeg_frames(camera.source_url),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.get("/stream/default")
async def stream_default_camera(db: AsyncSession = Depends(get_db)):
    from app.services.vision_service import VisionService
    svc = VisionService()
    source = await _global_camera_source(db)
    return StreamingResponse(
        svc.mjpeg_frames(source),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
