import base64
import time
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from app.core.compute import torch_device
from app.core.settings import settings


async def _get_vision_config(session_factory=None) -> dict:
    """Read vision.* keys from system_config, fall back to settings."""
    try:
        if session_factory is None:
            from app.core.database import AsyncSessionLocal

            session_factory = AsyncSessionLocal
        from app.repositories.config_repo import ConfigRepository

        async with session_factory() as db:
            repo = ConfigRepository(db)
            provider = await repo.get("vision.provider")
            api_key = await repo.get("vision.gemini_api_key")
            weights = await repo.get("vision.yolo_weights")
            confidence = await repo.get("vision.yolo_confidence")
            frames = await repo.get("vision.yolo_frames")

        return {
            "provider": provider or ("gemini" if settings.gemini_api_key else "yolo"),
            "gemini_api_key": api_key or settings.gemini_api_key or "",
            "yolo_weights": weights or settings.yolo_weights,
            "yolo_confidence": float(confidence) if confidence is not None else 0.6,
            "yolo_frames": int(frames) if frames is not None else 10,
        }
    except Exception:
        return {
            "provider": "gemini" if settings.gemini_api_key else "yolo",
            "gemini_api_key": settings.gemini_api_key or "",
            "yolo_weights": settings.yolo_weights,
            "yolo_confidence": 0.6,
            "yolo_frames": 10,
        }


class VisionService:
    def __init__(self):
        self.device = torch_device()
        self._model: YOLO | None = None

    def _get_model(self, weights_path: str) -> YOLO:
        path = Path(weights_path)
        if not path.exists():
            raise FileNotFoundError(f"Peso YOLO não encontrado: {path}")
        if self._model is None:
            self._model = YOLO(str(path))
        return self._model

    @staticmethod
    def _open_cap(source: str | int) -> cv2.VideoCapture:
        if isinstance(source, str) and source.isdigit():
            source = int(source)
        return cv2.VideoCapture(source)

    def capture_frame(self, source: str | int) -> np.ndarray | None:
        cap = self._open_cap(source)
        if not cap.isOpened():
            return None
        ret, frame = cap.read()
        cap.release()
        return frame if ret else None

    def yolo_describe(
        self,
        source: str | int,
        weights_path: str | None = None,
        frames: int = 10,
        delay: float = 0.2,
        conf: float = 0.6,
    ) -> str:
        wp = weights_path or settings.yolo_weights
        cap = self._open_cap(source)
        if not cap.isOpened():
            return "Não foi possível acessar a câmera."

        try:
            model = self._get_model(wp)
        except FileNotFoundError:
            cap.release()
            return (
                "Camera acessivel, mas o modelo YOLO nao esta instalado em "
                f"{wp}. Configure GEMINI_API_KEY para descricao visual "
                "ou adicione o arquivo de pesos no container."
            )
        instances: dict[str, list[int]] = defaultdict(list)

        try:
            for _ in range(frames):
                ret, frame = cap.read()
                if not ret:
                    continue
                frame = cv2.resize(frame, (1280, 720))
                results = model(frame, device=0 if self.device == "cuda" else self.device)
                names = results[0].names
                count: dict[str, int] = defaultdict(int)
                for box in results[0].boxes:
                    confidence = float(
                        box.conf[0] if hasattr(box.conf, "__len__") else box.conf
                    )
                    if confidence < conf:
                        continue
                    cls_id = int(
                        box.cls[0] if hasattr(box.cls, "__len__") else box.cls
                    )
                    count[names[cls_id]] += 1
                for label, qty in count.items():
                    instances[label].append(qty)
                time.sleep(delay)
        finally:
            cap.release()

        if not instances:
            return "Nenhum objeto foi detectado após múltiplas capturas."

        parts = []
        for label, occurrences in sorted(instances.items()):
            avg = sum(occurrences) / len(occurrences)
            parts.append("um(a) " + label if avg < 1.5 else f"múltiplos(as) {label}s")

        return "Na imagem foram detectados: " + ", ".join(parts) + "."

    @staticmethod
    def frame_to_base64(frame: np.ndarray) -> str:
        _, buffer = cv2.imencode(".jpg", frame)
        return base64.b64encode(buffer).decode("utf-8")

    async def gemini_describe(self, source: str | int, api_key: str) -> str:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage

        frame = self.capture_frame(source)
        if frame is None:
            return "Não foi possível capturar imagem da câmera."

        image_b64 = self.frame_to_base64(frame)
        model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
        )
        response = await model.ainvoke([
            HumanMessage(content=[
                {
                    "type": "text",
                    "text": (
                        "Você é o DomusMind, assistente doméstico. "
                        "Descreva detalhadamente o que você vê nesta imagem "
                        "de câmera de segurança em português do Brasil. "
                        "Inclua pessoas, objetos, atividades e qualquer coisa relevante."
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                },
            ])
        ])
        return str(response.content).strip()

    async def describe(
        self,
        source: str | int | None = None,
        camera_name: str | None = None,
        use_gemini: bool = True,
        db_session_factory=None,
    ) -> str:
        """Primary entry point. Resolves camera by name if provided, then uses DB config."""
        # Resolve source from camera name if given
        if camera_name and source is None:
            try:
                if db_session_factory is None:
                    from app.core.database import AsyncSessionLocal

                    db_session_factory = AsyncSessionLocal
                from app.repositories.room_repo import RoomRepository

                async with db_session_factory() as db:
                    cam = await RoomRepository(db).get_camera_by_name(camera_name)
                if cam:
                    source = cam.source_url
            except Exception:
                pass

        cfg = await _get_vision_config(db_session_factory)
        src = source if source is not None else settings.default_camera_source

        if use_gemini and cfg["provider"] == "gemini" and cfg["gemini_api_key"]:
            try:
                return await self.gemini_describe(src, cfg["gemini_api_key"])
            except Exception:
                pass  # fall through to YOLO

        return self.yolo_describe(
            src,
            weights_path=cfg["yolo_weights"],
            frames=cfg["yolo_frames"],
            conf=cfg["yolo_confidence"],
        )

    def mjpeg_frames(self, source: str | int):
        """Generator that yields MJPEG bytes for HTTP streaming."""
        cap = self._open_cap(source)
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                _, buffer = cv2.imencode(".jpg", frame)
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + buffer.tobytes()
                    + b"\r\n"
                )
        finally:
            cap.release()
