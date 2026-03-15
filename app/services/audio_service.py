import numpy as np
import sounddevice as sd
import torch
from faster_whisper import WhisperModel

from app.core.settings import settings


class AudioService:
    def __init__(self):
        self.sample_rate = settings.audio_sample_rate
        self.whisper_model_name = settings.whisper_model
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compute_type = settings.whisper_compute_type
        self._model = None

    def _get_model(self) -> WhisperModel:
        if self._model is None:
            self._model = WhisperModel(
                self.whisper_model_name,
                compute_type=self.compute_type,
                device=self.device,
            )
        return self._model

    def capture_audio_and_transcribe_continuous(
        self,
        max_duration: int = 30,
        silence_duration: int = 2,
        threshold: float = 0.005,
        language: str = "pt",
    ) -> str:
        model = self._get_model()

        buffer: list[np.ndarray] = []
        is_recording = False
        silence_counter = 0
        chunk_duration = 0.2
        chunk_samples = int(self.sample_rate * chunk_duration)
        max_chunks = int(max_duration / chunk_duration)
        silence_limit_chunks = int(silence_duration / chunk_duration)

        stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
        )

        try:
            stream.start()

            for _ in range(max_chunks):
                audio_chunk, _ = stream.read(chunk_samples)
                audio_chunk = np.squeeze(audio_chunk)
                rms = np.sqrt(np.mean(audio_chunk**2))

                if rms > threshold:
                    is_recording = True
                    silence_counter = 0
                    buffer.append(audio_chunk)
                elif is_recording:
                    silence_counter += 1
                    buffer.append(audio_chunk)

                    if silence_counter >= silence_limit_chunks:
                        break
        finally:
            stream.stop()
            stream.close()

        if not buffer:
            return ""

        audio = np.concatenate(buffer)
        audio = np.clip(audio, -1.0, 1.0)

        segments, _ = model.transcribe(
            audio,
            language=language,
            beam_size=5,
            best_of=5,
            vad_filter=True,
        )

        return " ".join(seg.text for seg in segments).strip()