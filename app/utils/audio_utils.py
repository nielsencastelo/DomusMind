# utilitários de áudio
import sounddevice as sd
import numpy as np
import tempfile
import scipy.io.wavfile

def gravar_audio(device_id, duracao=5, fs=16000):
    audio = sd.rec(int(duracao * fs), samplerate=fs, channels=1, dtype='int16', device=device_id)
    sd.wait()
    return audio.squeeze(), fs

def salvar_temp_wav(audio, fs):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    scipy.io.wavfile.write(tmp.name, fs, audio)
    return tmp.name
