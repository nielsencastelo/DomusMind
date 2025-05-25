
# -*- coding: utf-8 -*-
from utils.audio_utils import capture_audio_and_transcribe # WhisperModel
from utils.voz_utils import speak_text_with_mms # Facebook mms-tts-po
from utils.vision_utils import capture_image_and_describe # YOLOv8
from utils.llm_utils import ask_llm_ollama 

from langchain_core.messages import AIMessage, HumanMessage

# SAMPLE_RATE = 16000
# DURATION = 5
# DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# print(f"🖥️ Dispositivo: {DEVICE}")

modelos_disponiveis = ["Llama 3.2", "phi4", "gemma3:27b"]
escolha = 1

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
#     os.remove(audio_path)

#     transcription = " ".join([seg.text for seg in segments])
#     print(f"📝 Transcrição: {transcription}")
#     return transcription.strip()

# def capture_image_and_describe():
#     model = YOLO("yolov8n.pt")
#     cap = cv2.VideoCapture(0)
#     ret, frame = cap.read()
#     cap.release()
#     if not ret:
#         return "Nenhuma imagem capturada."

#     results = model(frame)
#     names = results[0].names
#     boxes = results[0].boxes

#     objetos = []
#     for box in boxes:
#         cls_id = int(box.cls)
#         label = names[cls_id]
#         conf = float(box.conf)
#         objetos.append((label, conf))

#     if not objetos:
#         return "Nenhum objeto detectado."

#     descricoes = []
#     for label, conf in objetos:
#         conf_percent = int(conf * 100)
#         if conf >= 0.8:
#             descricoes.append(f"{label} ({conf_percent}%)")
#         elif conf >= 0.4:
#             descricoes.append(f"possível {label} ({conf_percent}%)")
#         else:
#             descricoes.append(f"{label} incerto ({conf_percent}%)")

#     return f"Objetos detectados: {', '.join(descricoes)}."

# def speak_text_with_mms(text):
#     from transformers import VitsModel, AutoTokenizer
#     import torch
#     import numpy as np
#     import sounddevice as sd

#     model = VitsModel.from_pretrained("facebook/mms-tts-por")
#     tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-por")

#     inputs = tokenizer(text, return_tensors="pt")
#     with torch.no_grad():
#         output = model(**inputs).waveform

#     audio = output.squeeze().numpy()
#     audio = audio / np.max(np.abs(audio))  # normaliza para [-1, 1]

#     print("🔊 Reproduzindo resposta...")
#     sd.play(audio, samplerate=model.config.sampling_rate)
#     sd.wait()



def main():
    history = []
    while True:
        user_input = capture_audio_and_transcribe()
        if not user_input or len(user_input.strip()) <= 1:
            print("⏭️ Nada foi falado, aguardando...")
            continue

        if "sair" in user_input.lower():
            print("👋 Encerrando assistente.")
            break

        vision_desc = capture_image_and_describe()
        full_prompt = f"{user_input}\nVisão: {vision_desc}"
        history.append(HumanMessage(content=full_prompt))

        modelo_escolhido = modelos_disponiveis[escolha - 1] if 0 < escolha <= len(modelos_disponiveis) else "phi4"
        print(f"✅ Modelo selecionado: {modelo_escolhido}")
        llm_response = ask_llm_ollama(full_prompt, history, modelo_escolhido)
        print("🤖:", llm_response)
        speak_text_with_mms(llm_response)

        history.append(HumanMessage(content=user_input))
        history.append(AIMessage(content=llm_response))

if __name__ == "__main__":
    main()
