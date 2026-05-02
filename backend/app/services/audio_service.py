import numpy as np
import torch
from faster_whisper import WhisperModel

from app.core.compute import torch_device
from app.core.settings import settings


class AudioService:
    def __init__(
        self,
        sample_rate: int | None = None,
        model_name: str | None = None,
        compute_type: str | None = None,
    ):
        self.sample_rate = sample_rate or settings.audio_sample_rate
        self.model_name = model_name or settings.whisper_model
        self.compute_type = compute_type or settings.whisper_compute_type
        self.device = torch_device()
        self._model: WhisperModel | None = None

    def _get_model(self) -> WhisperModel:
        if self._model is None:
            self._model = WhisperModel(
                self.model_name,
                compute_type=self.compute_type,
                device=self.device,
            )
        return self._model

    def transcribe_file(self, path: str, language: str = "pt") -> str:
        model = self._get_model()
        segments, _ = model.transcribe(
            path,
            language=language,
            beam_size=5,
            best_of=5,
            vad_filter=True,
        )
        return " ".join(s.text for s in segments).strip()

    def transcribe_array(self, audio: np.ndarray, language: str = "pt") -> str:
        model = self._get_model()
        segments, _ = model.transcribe(
            audio,
            language=language,
            beam_size=5,
            best_of=5,
            vad_filter=True,
        )
        return " ".join(s.text for s in segments).strip()

    def capture_and_transcribe(
        self,
        max_duration: int = 30,
        silence_duration: int = 2,
        threshold: float = 0.005,
        language: str = "pt",
    ) -> str:
        import sounddevice as sd

        chunk_duration = 0.2
        chunk_samples = int(self.sample_rate * chunk_duration)
        max_chunks = int(max_duration / chunk_duration)
        silence_limit = int(silence_duration / chunk_duration)

        buffer: list[np.ndarray] = []
        is_recording = False
        silence_counter = 0

        stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
        )

        try:
            stream.start()
            for _ in range(max_chunks):
                chunk, _ = stream.read(chunk_samples)
                chunk = np.squeeze(chunk)
                rms = float(np.sqrt(np.mean(chunk**2)))

                if rms > threshold:
                    is_recording = True
                    silence_counter = 0
                    buffer.append(chunk)
                elif is_recording:
                    silence_counter += 1
                    buffer.append(chunk)
                    if silence_counter >= silence_limit:
                        break
        finally:
            stream.stop()
            stream.close()

        if not buffer:
            return ""

        audio = np.clip(np.concatenate(buffer), -1.0, 1.0)
        return self.transcribe_array(audio, language)
