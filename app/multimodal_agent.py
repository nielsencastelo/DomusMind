
import os
import numpy as np
import sounddevice as sd
import tempfile
import scipy.io.wavfile
import cv2
import torch
import io
import wave
from faster_whisper import WhisperModel
from transformers import VitsModel, AutoTokenizer
from ultralytics import YOLO
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage

SAMPLE_RATE = 16000
DURATION = 5
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"🖥️ Dispositivo: {DEVICE}")

modelos_disponiveis = ["Llama 3.2", "phi4", "gemma3:27b"]
escolha = 1

def model_ollama(model, temperature=0.1):
    return ChatOllama(model=model.lower().replace(" ", ""), temperature=temperature)

def model_response(user_query, chat_history, model_name):
    try:
        llm = model_ollama(model_name)

        system_prompt = """
        Você é um assistente doméstico com percepção visual e auditiva.
        - Use a descrição da câmera, que inclui objetos detectados e seus níveis de confiança.
        - Avalie se o que foi detectado é confiável ou não.
        - Baseie sua resposta na fala do usuário e nos objetos com maior confiança.
        - Ignore objetos com baixa confiança, ou mencione que são incertos.
        - Seja claro, educado e direto. Resposta curta e simples.
        Fale sempre em português, como se estivesse presente no ambiente.
        """

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}")
        ])

        chain = prompt_template | llm | StrOutputParser()
        response = chain.invoke({"chat_history": chat_history, "input": user_query})
        return response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        print("Erro no modelo:", e)
        return "❌ Desculpe, não consegui entender ou realizar essa ação. Por favor, tente novamente."

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

def capture_image_and_describe():
    model = YOLO("yolov8n.pt")
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return "Nenhuma imagem capturada."

    results = model(frame)
    names = results[0].names
    boxes = results[0].boxes

    objetos = []
    for box in boxes:
        cls_id = int(box.cls)
        label = names[cls_id]
        conf = float(box.conf)
        objetos.append((label, conf))

    if not objetos:
        return "Nenhum objeto detectado."

    descricoes = []
    for label, conf in objetos:
        conf_percent = int(conf * 100)
        if conf >= 0.8:
            descricoes.append(f"{label} ({conf_percent}%)")
        elif conf >= 0.4:
            descricoes.append(f"possível {label} ({conf_percent}%)")
        else:
            descricoes.append(f"{label} incerto ({conf_percent}%)")

    return f"Objetos detectados: {', '.join(descricoes)}."

def speak_text_with_mms(text):
    from transformers import VitsModel, AutoTokenizer
    import torch
    import numpy as np
    import sounddevice as sd

    model = VitsModel.from_pretrained("facebook/mms-tts-por")
    tokenizer = AutoTokenizer.from_pretrained("facebook/mms-tts-por")

    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        output = model(**inputs).waveform

    audio = output.squeeze().numpy()
    audio = audio / np.max(np.abs(audio))  # normaliza para [-1, 1]

    print("🔊 Reproduzindo resposta...")
    sd.play(audio, samplerate=model.config.sampling_rate)
    sd.wait()



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
        llm_response = model_response(full_prompt, history, modelo_escolhido)
        print("🤖:", llm_response)
        speak_text_with_mms(llm_response)

        history.append(HumanMessage(content=user_input))
        history.append(AIMessage(content=llm_response))

if __name__ == "__main__":
    main()
