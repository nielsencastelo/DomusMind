# from transformers import VitsModel, AutoTokenizer
import torch
import numpy as np
import sounddevice as sd
from TTS.api import TTS

device = "cuda" if torch.cuda.is_available() else "cpu"

tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False).to(device)

def speak_text_with_tts(text):
    wav = tts.tts(text = text, speaker_wav="Voz_Nielsen.wav", language="pt", )
    sr = getattr(getattr(tts, "synthesizer", None), "output_sample_rate", None) or 24000

    wav = np.asarray(wav).astype(np.float32).reshape(-1)
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