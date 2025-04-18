from transformers import VitsModel, AutoTokenizer
import torch
import io
from IPython.display import Audio
import scipy.io.wavfile
import numpy as np
from pydub import AudioSegment
from IPython.display import Audio

# Carrega modelo e tokenizer
model = VitsModel.from_pretrained("facebook/mms-tts-por")
tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-por")


def falar_texto(texto):
    
    inputs = tokenizer(texto, return_tensors="pt")
    with torch.no_grad():
        output = model(**inputs).waveform

    # Normaliza e converte para int16
    audio = output.squeeze().numpy()
    audio = audio / np.max(np.abs(audio))  # normaliza para [-1, 1]
    audio_int16 = (audio * 32767).astype(np.int16)

    # buffer = io.BytesIO()
    # scipy.io.wavfile.write(buffer, rate=model.config.sampling_rate, data=audio_int16)
    
    return audio_int16, model

