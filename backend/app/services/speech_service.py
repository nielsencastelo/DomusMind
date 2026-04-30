import re
from pathlib import Path

import numpy as np
import sounddevice as sd
import torch
from TTS.api import TTS

from app.core.compute import torch_device
from app.core.settings import settings


class SpeechService:
    def __init__(self):
        self.device = torch_device()
        self.speaker_wav = Path(settings.tts_speaker_wav)
        self._tts: TTS | None = None

    def _get_tts(self) -> TTS:
        if self._tts is None:
            self._tts = TTS(
                model_name=settings.tts_model_name,
                progress_bar=False,
            ).to(self.device)
        return self._tts

    @staticmethod
    def _clean(text: str) -> str:
        return re.sub(r"\.(\s|$)", r"\1", text)

    def speak(self, text: str) -> None:
        if not self.speaker_wav.exists():
            raise FileNotFoundError(
                f"Áudio de referência não encontrado: {self.speaker_wav}"
            )
        tts = self._get_tts()
        wav = tts.tts(
            text=self._clean(text),
            speaker_wav=str(self.speaker_wav),
            language=settings.tts_language,
        )
        sr = (
            getattr(getattr(tts, "synthesizer", None), "output_sample_rate", None)
            or settings.tts_fallback_sr
        )
        audio = np.asarray(wav, dtype=np.float32).reshape(-1)
        sd.play(audio, sr)
        sd.wait()

    def synthesize_to_bytes(self, text: str) -> tuple[bytes, int]:
        """Return raw PCM bytes and sample rate (for HTTP audio response)."""
        if not self.speaker_wav.exists():
            raise FileNotFoundError(
                f"Áudio de referência não encontrado: {self.speaker_wav}"
            )
        tts = self._get_tts()
        wav = tts.tts(
            text=self._clean(text),
            speaker_wav=str(self.speaker_wav),
            language=settings.tts_language,
        )
        sr = (
            getattr(getattr(tts, "synthesizer", None), "output_sample_rate", None)
            or settings.tts_fallback_sr
        )
        audio = np.asarray(wav, dtype=np.float32)
        pcm = (audio * 32767).astype(np.int16).tobytes()
        return pcm, sr
