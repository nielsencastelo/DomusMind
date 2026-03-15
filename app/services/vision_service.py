import time
from collections import defaultdict
from pathlib import Path

import cv2
from ultralytics import YOLO

from app.adapters.camera_adapter import CameraAdapter
from app.core.settings import settings


class VisionService:
    def __init__(self):
        self.weights_path = Path(settings.yolo_weights)
        self.default_camera = settings.default_camera_source
        self.camera_adapter = CameraAdapter()
        self._model = None

    def _get_model(self) -> YOLO:
        if self._model is None:
            self._model = YOLO(str(self.weights_path))
        return self._model

    def capture_and_describe(
        self,
        camera_source: str | int | None = None,
        frames_to_capture: int = 10,
        delay_between_frames: float = 0.2,
        conf_threshold: float = 0.6,
    ) -> str:
        source = camera_source if camera_source is not None else self.default_camera
        cap = self.camera_adapter.open(source)

        if not cap.isOpened():
            return "Não foi possível acessar a câmera."

        model = self._get_model()
        instancias = defaultdict(list)

        for _ in range(frames_to_capture):
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.resize(frame, (1280, 720))
            results = model(frame)
            names = results[0].names
            boxes = results[0].boxes
            count_this_frame = defaultdict(int)

            for box in boxes:
                conf = float(box.conf[0]) if hasattr(box.conf, "__len__") else float(box.conf)
                if conf < conf_threshold:
                    continue

                cls_id = int(box.cls[0]) if hasattr(box.cls, "__len__") else int(box.cls)
                label = names[cls_id]
                count_this_frame[label] += 1

            for label, qtd in count_this_frame.items():
                instancias[label].append(qtd)

            time.sleep(delay_between_frames)

        cap.release()

        if not instancias:
            return "Nenhum objeto foi detectado após múltiplas capturas."

        descricoes = []
        for label, ocorrencias in sorted(instancias.items()):
            media = sum(ocorrencias) / len(ocorrencias)
            if media < 1.5:
                descricoes.append(f"um(a) {label}")
            else:
                descricoes.append(f"múltiplos(as) {label}s")

        return "Na imagem foram detectados: " + ", ".join(descricoes) + "."