import asyncio
import time
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

from utils.audio_utils import capture_audio_and_transcribe_continuous as capture_audio_and_transcribe
from utils.voz_utils import speak_text_with_mms
from utils.vision_utils import capture_image_and_describe
from utils.llm_utils import ask_llm_ollama
from utils.nlp_utils import check_vision_intent, check_wake_word, WAKE_WORDS
from langchain_core.messages import AIMessage, HumanMessage

modelos_disponiveis = ["Llama 3.2", "phi4", "gemma3:27b"]
escolha = 1
executor = ThreadPoolExecutor(max_workers=4)

@lru_cache(maxsize=50)
def cached_llm_response(prompt: str, model: str):
    return ask_llm_ollama(prompt, [], model)

async def handle_activation_response(wake_input: str):
    if any(w in wake_input.lower() for w in WAKE_WORDS):
        saudacao = "Oi, estou aqui Nielsen."
        print(f"🤖: {saudacao}")
        await asyncio.to_thread(speak_text_with_mms, saudacao)
        # Aguarda a fala ser concluída naturalmente

async def main_async():
    history = []

    while True:
        print("🎧 Aguardando palavra de ativação...")

        # 1. Espera wake word
        while True:
            wake_input = await asyncio.to_thread(capture_audio_and_transcribe)
            if not wake_input or len(wake_input.strip()) <= 1:
                continue

            if "sair" in wake_input.lower():
                print(wake_input)
                print("👋 Encerrando assistente.")
                return

            if check_wake_word(wake_input):
                print(f"🚀 Palavra de ativação detectada: {wake_input}")
                await handle_activation_response(wake_input)
                break

            print("⏳ Nenhuma palavra de ativação detectada. Continuando escuta...")

        # 2. Grava comando do usuário
        print("🎙️ Escutando comando...")
        user_input = await asyncio.to_thread(capture_audio_and_transcribe)

        if not user_input or len(user_input.strip()) <= 1:
            print("⚠️ Nenhum comando detectado.")
            continue

        cleaned_input = user_input.strip()

        # 3. Visão (se necessário) em paralelo
        if check_vision_intent(cleaned_input):
            print("🧠 Visão necessária. Capturando imagem...")
            vision_desc = await asyncio.to_thread(capture_image_and_describe)
            print('📸 Descrição visão:', vision_desc)
            full_prompt = f"{cleaned_input}\nVisão: {vision_desc}"
        else:
            full_prompt = cleaned_input

        # 4. Chamada ao LLM com histórico
        history.append(HumanMessage(content=full_prompt))
        modelo_escolhido = modelos_disponiveis[escolha]
        print(f"✅ Modelo selecionado: {modelo_escolhido}")

        llm_response = await asyncio.to_thread(cached_llm_response, full_prompt, modelo_escolhido)
        print("🤖:", llm_response)

        # 5. Fala a resposta do LLM
        await asyncio.to_thread(speak_text_with_mms, llm_response)

        # 6. Atualiza histórico
        history.append(HumanMessage(content=cleaned_input))
        history.append(AIMessage(content=llm_response))

# Entry point
if __name__ == "__main__":
    asyncio.run(main_async())
