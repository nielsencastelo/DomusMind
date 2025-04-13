# fala com TTS Coqui
from TTS.api import TTS
import os
import tempfile
import sounddevice as sd
import soundfile as sf

tts = TTS(model_name="tts_models/pt/cv/vits", progress_bar=False, gpu=False)

def falar_texto(texto):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
        path = tmpfile.name
        tts.tts_to_file(text=texto, file_path=path)
        data, fs = sf.read(path)
        sd.play(data, fs)
        sd.wait()
        os.remove(path)
