from transformers import VitsModel, AutoTokenizer
import torch
import numpy as np
import sounddevice as sd

model = VitsModel.from_pretrained("facebook/mms-tts-por")
tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-por")

def speak_text_with_mms(text):
    
    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        output = model(**inputs).waveform

    audio = output.squeeze().numpy()
    audio = audio / np.max(np.abs(audio))  # normaliza para [-1, 1]

    print("🔊 Reproduzindo resposta...")
    sd.play(audio, samplerate=model.config.sampling_rate)
    sd.wait()


