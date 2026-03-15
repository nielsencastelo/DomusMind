import re
from pathlib import Path

import numpy as np
import sounddevice as sd
import torch
from TTS.api import TTS

from app.core.settings import settings


class SpeechService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = settings.tts_model_name
        self.speaker_wav = Path(settings.tts_speaker_wav)
        self.language = settings.tts_language
        self.fallback_sr = 24000
        self._tts = None

    def _get_tts(self):
        if self._tts is None:
            self._tts = TTS(
                model_name=self.model_name,
                progress_bar=False,
            ).to(self.device)
        return self._tts

    @staticmethod
    def limpa_pontuacao(texto: str) -> str:
        return re.sub(r"\.(\s|$)", r"\1", texto)

    def speak_text_with_tts(self, text: str) -> None:
        if not self.speaker_wav.exists():
            raise FileNotFoundError(f"Áudio de referência não encontrado: {self.speaker_wav}")

        tts = self._get_tts()

        wav = tts.tts(
            text=self.limpa_pontuacao(text),
            speaker_wav=str(self.speaker_wav),
            language=self.language,
        )

        sr = getattr(getattr(tts, "synthesizer", None), "output_sample_rate", None) or self.fallback_sr
        wav = np.asarray(wav, dtype=np.float32).reshape(-1)

        sd.play(wav, sr)
        sd.wait()