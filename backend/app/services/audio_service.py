import numpy as np
import sounddevice as sd
import torch
from faster_whisper import WhisperModel

from app.core.settings import settings


class AudioService:
    def __init__(self):
        self.sample_rate = settings.audio_sample_rate
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model: WhisperModel | None = None

    def _get_model(self) -> WhisperModel:
        if self._model is None:
            self._model = WhisperModel(
                settings.whisper_model,
                compute_type=settings.whisper_compute_type,
                device=self.device,
            )
        return self._model

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
