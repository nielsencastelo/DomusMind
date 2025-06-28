
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

# def capture_audio_and_transcribe():
#     print("🎙️ Gravando áudio...")
#     audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
#     sd.wait()
#     print("✅ Gravação concluída.")

#     audio = np.squeeze(audio)
#     audio = np.clip(audio, -1.0, 1.0)
#     audio_int16 = (audio * 32767).astype(np.int16)

#     with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
#         scipy.io.wavfile.write(tmp.name, SAMPLE_RATE, audio_int16)
#         audio_path = tmp.name

#     model = WhisperModel("medium", compute_type="float32", device=DEVICE)
#     segments, info = model.transcribe(audio_path, language="pt")
    
#     # os.remove(audio_path)
#     if transcription.strip():
#         os.remove(audio_path)
#     else:
#         print(f"💾 Áudio salvo para debug: {audio_path}")


#     transcription = " ".join([seg.text for seg in segments])
#     print(f"📝 Transcrição: {transcription}")
#     return transcription.strip()


def capture_audio_and_transcribe_continuous(
    sample_rate=16000,        # taxa de amostragem do áudio (Hz)
    max_duration=15,          # duração máxima da gravação (segundos)
    silence_duration=1.5,     # quanto tempo de silêncio para parar (segundos)
    threshold=0.005             # limiar de volume para considerar silêncio
):
    print("🎧 Aguardando início da fala...")

    model = WhisperModel("medium", compute_type="float32", device=DEVICE)

    buffer = []
    is_recording = False
    silence_counter = 0
    chunk_duration = 0.2  # segundos por chunk
    chunk_samples = int(sample_rate * chunk_duration)
    max_chunks = int(max_duration / chunk_duration)
    silence_limit_chunks = int(silence_duration / chunk_duration)

    stream = sd.InputStream(samplerate=sample_rate, channels=1, dtype='float32')
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

    stream.stop()

    if not buffer:
        print("🕐 Nenhuma fala detectada.")
        return ""

    audio = np.concatenate(buffer)
    audio = np.clip(audio, -1.0, 1.0)
    audio_int16 = (audio * 32767).astype(np.int16)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        scipy.io.wavfile.write(tmp.name, sample_rate, audio_int16)
        audio_path = tmp.name

    segments, info = model.transcribe(audio_path, language="pt")
    os.remove(audio_path)

    transcription = " ".join([seg.text for seg in segments])
    print(f"📝 Transcrição: {transcription}")
    return transcription.strip()

