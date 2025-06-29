import asyncio
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

from agents.audio_agent import AudioAgent
from agents.speech_agent import SpeechAgent
from agents.vision_agent import VisionAgent
from agents.llm_agent import LLMAgent

from utils.nlp_utils import check_vision_intent, check_wake_word, WAKE_WORDS
from utils.nlp_utils import check_exit_command
from langchain_core.messages import AIMessage, HumanMessage

# Modelos disponíveis e escolha
modelos_disponiveis = ["Llama 3.2", "phi4", "gemma3:27b"]
escolha = 1  # índice do modelo selecionado

# Executor para threads (opcional, pois asyncio.to_thread já abstrai isso)
executor = ThreadPoolExecutor(max_workers=4)

# Instanciação dos agentes
audio_agent = AudioAgent()
speech_agent = SpeechAgent()
vision_agent = VisionAgent()
llm_agent = LLMAgent(model_name=modelos_disponiveis[escolha])

@lru_cache(maxsize=50)
def cached_llm_response(prompt: str, model: str):
    return llm_agent.ask(prompt, [])

async def handle_activation_response(wake_input: str):
    if any(w in wake_input.lower() for w in WAKE_WORDS):
        saudacao = "Oi, estou aqui Nielsen."
        print(f"🤖: {saudacao}")
        await asyncio.to_thread(speech_agent.speak, saudacao)

async def main_async():
    history = []

    while True:
        print("🎧 Aguardando palavra de ativação...")

        # 1. Espera wake word
        while True:
            wake_input = await asyncio.to_thread(audio_agent.listen_and_transcribe)
            if not wake_input or len(wake_input.strip()) <= 1:
                continue

            if check_exit_command(wake_input):
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
        user_input = await asyncio.to_thread(audio_agent.listen_and_transcribe)

        if not user_input or len(user_input.strip()) <= 1:
            print("⚠️ Nenhum comando detectado.")
            continue

        cleaned_input = user_input.strip()

        # 3. Visão (se necessário) em paralelo
        if check_vision_intent(cleaned_input):
            print("🧠 Visão necessária. Capturando imagem...")
            vision_desc = await asyncio.to_thread(vision_agent.capture_and_describe)
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
        await asyncio.to_thread(speech_agent.speak, llm_response)

        # 6. Atualiza histórico
        history.append(HumanMessage(content=cleaned_input))
        history.append(AIMessage(content=llm_response))

# Entry point
if __name__ == "__main__":
    asyncio.run(main_async())
