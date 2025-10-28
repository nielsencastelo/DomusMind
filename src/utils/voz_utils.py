# from transformers import VitsModel, AutoTokenizer
from pathlib import Path
import torch
import numpy as np
import sounddevice as sd
from TTS.api import TTS
import re

device = "cuda" if torch.cuda.is_available() else "cpu"

# ✔️ defina a pasta e o arquivo do áudio de referência
SPEAKER_DIR = Path(r"E:\Projetos\pinica_ia\src\model")     # raw string evita escapes
SPEAKER_WAV = SPEAKER_DIR / "Voz_Nielsen.wav"              # Path independe do SO

# opcional: valide existência do arquivo
if not SPEAKER_WAV.exists():
    raise FileNotFoundError(f"Não encontrei o áudio de referência: {SPEAKER_WAV}")

tts = TTS(
    model_name="tts_models/multilingual/multi-dataset/xtts_v2",
    progress_bar=False
).to(device)


def limpa_pontuacao(texto):
    return re.sub(r'\.(\s|$)', r'\1', texto)

def speak_text_with_tts(text: str, speaker_path: Path = SPEAKER_WAV, fallback_sr: int = 24000):
    # importante: passar str(Path) para a API
    wav = tts.tts(
        text=limpa_pontuacao(text),
        speaker_wav=str(speaker_path),
        language="pt",
    )
    sr = getattr(getattr(tts, "synthesizer", None), "output_sample_rate", None) or fallback_sr
    wav = np.asarray(wav, dtype=np.float32).reshape(-1)
    sd.play(wav, sr)
    sd.wait()



# model = VitsModel.from_pretrained("facebook/mms-tts-por")
# tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-por")

# def speak_text_with_mms(text):
    
#     inputs = tokenizer(text, return_tensors="pt")
#     with torch.no_grad():
#         output = model(**inputs).waveform

#     audio = output.squeeze().numpy()
#     audio = audio / np.max(np.abs(audio))  # normaliza para [-1, 1]

#     print("🔊 Reproduzindo resposta...")
#     sd.play(audio, samplerate=model.config.sampling_rate)
#     sd.wait()