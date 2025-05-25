# -*- coding: utf-8 -*-

# import json
# import time
# from room_module import processar_comodo

# with open("configs/rooms.json") as f:
#     rooms = json.load(f)

# while True:
#     for nome, config in rooms.items():
#         try:
#             processar_comodo(nome, config)
#         except Exception as e:
#             print(f"[{nome}] Erro: {e}")
#     time.sleep(20)


from utils.audio_utils import capture_audio_and_transcribe # WhisperModel
from utils.voz_utils import speak_text_with_mms # Facebook mms-tts-po
from utils.vision_utils import capture_image_and_describe # YOLOv8
from utils.llm_utils import ask_llm_ollama 
from utils.nlp_utils import check_vision_intent, check_wake_word, WAKE_WORDS
from langchain_core.messages import AIMessage, HumanMessage

modelos_disponiveis = ["Llama 3.2", "phi4", "gemma3:27b"]
escolha = 1

def main():
    history = []
    while True:
        print("🎧 Aguardando comando...")
        user_input = capture_audio_and_transcribe()

        if not user_input or len(user_input.strip()) <= 1:
            print("⏭️ Nada foi falado, aguardando...")
            continue

        if "sair" in user_input.lower():
            print("👋 Encerrando assistente.")
            break

        if not check_wake_word(user_input):
            print("🕐 Aguardando palavra de ativação...")
            continue

        print(f"🚀 Palavra de ativação detectada: {user_input}")

        # (Opcional) Remove wake word do texto para deixar o prompt limpo
        cleaned_input = user_input
        for wake_word in WAKE_WORDS:
            cleaned_input = cleaned_input.lower().replace(wake_word, "").strip()

        # Verifica se há intenção de usar visão
        if check_vision_intent(cleaned_input):
            vision_desc = capture_image_and_describe()
            full_prompt = f"{cleaned_input}\nVisão: {vision_desc}"
        else:
            full_prompt = cleaned_input

        history.append(HumanMessage(content=full_prompt))

        modelo_escolhido = modelos_disponiveis[escolha - 1] if 0 < escolha <= len(modelos_disponiveis) else "phi4"
        print(f"✅ Modelo selecionado: {modelo_escolhido}")

        llm_response = ask_llm_ollama(full_prompt, history, modelo_escolhido)
        print("🤖:", llm_response)
        speak_text_with_mms(llm_response)

        history.append(HumanMessage(content=cleaned_input))
        history.append(AIMessage(content=llm_response))


if __name__ == "__main__":
    main()

