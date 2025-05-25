
import torch
import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import tempfile
import os
import scipy.io.wavfile

SAMPLE_RATE = 16000
DURATION = 5
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🖥️ Dispositivo para Whisper: {DEVICE}")

def capture_audio_and_transcribe():
    print("🎙️ Gravando áudio...")
    audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    print("✅ Gravação concluída.")

    audio = np.squeeze(audio)
    audio = np.clip(audio, -1.0, 1.0)
    audio_int16 = (audio * 32767).astype(np.int16)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        scipy.io.wavfile.write(tmp.name, SAMPLE_RATE, audio_int16)
        audio_path = tmp.name

    model = WhisperModel("medium", compute_type="float32", device=DEVICE)
    segments, info = model.transcribe(audio_path, language="pt")
    os.remove(audio_path)

    transcription = " ".join([seg.text for seg in segments])
    print(f"📝 Transcrição: {transcription}")
    return transcription.strip()


# def gravar_audio(device_id, duracao=5, fs=16000):
#     audio = sd.rec(int(duracao * fs), samplerate=fs, channels=1, dtype='int16', device=device_id)
#     sd.wait()
#     return audio.squeeze(), fs

# def salvar_temp_wav(audio, fs):
#     tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
#     scipy.io.wavfile.write(tmp.name, fs, audio)
#     return tmp.name
