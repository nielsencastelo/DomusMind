import asyncio
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

from agents.audio_agent import AudioAgent
from agents.speech_agent import SpeechAgent
from agents.vision_agent import VisionAgent
from agents.llm_agent import LLMAgent
from agents.search_agent import SearchAgent
from agents.intent_classifier_agent import IntentClassifierAgent

from langchain_core.messages import AIMessage, HumanMessage

modelos_disponiveis = ["Llama 3.2", "phi4", "gemma3:27b"]
escolha = 1

executor = ThreadPoolExecutor(max_workers=4)

# Agentes
audio_agent = AudioAgent()
speech_agent = SpeechAgent()
vision_agent = VisionAgent()
llm_agent = LLMAgent(model_name=modelos_disponiveis[escolha])
search_agent = SearchAgent()
intent_agent = IntentClassifierAgent()

@lru_cache(maxsize=50)
def cached_llm_response(prompt: str, model: str):
    return llm_agent.ask(prompt, [])

async def main_async():
    history = []

    while True:
        print("🎧 Aguardando comando com 'coca'...")

        user_input = await asyncio.to_thread(audio_agent.listen_and_transcribe)

        if not user_input or "coca" not in user_input.lower():
            continue  # Ignora comandos sem wake word

        cleaned_input = user_input.strip()
        print(f"📝 Comando com 'coca' detectado: {cleaned_input}")

        intent = await asyncio.to_thread(intent_agent.classify, user_input)

        if intent == "ignorar":
            print("🔇 Nenhuma wake word detectada. Ignorando comando.")
            continue

        if intent == "sair":
            saudacao = "Oi Nielsen, encerrando o programa."
            print(f"🤖: {saudacao}")
            await asyncio.to_thread(speech_agent.speak, saudacao)
            return

        elif intent == "pesquisa":
            saudacao = "Oi Nielsen, vou pesquisar isso pra você agora."
            print(f"🤖: {saudacao}")
            await asyncio.to_thread(speech_agent.speak, saudacao)

            print("🌐 Executando busca na web...")
            search_text, file_path = await asyncio.to_thread(
                search_agent.search_and_summarize, cleaned_input
            )

            prompt_busca = (
                f"O usuário pediu uma busca na internet sobre: '{cleaned_input}'.\n\n"
                f"Aqui estão os resultados:\n{search_text}\n\n"
                f"Resuma as informações mais relevantes em até 3 frases curtas e práticas."
            )

            history.append(HumanMessage(content=prompt_busca))
            llm_response = await asyncio.to_thread(
                cached_llm_response, prompt_busca, modelos_disponiveis[escolha]
            )
            print("🤖 (resumo da busca):", llm_response)

            await asyncio.to_thread(speech_agent.speak, llm_response)
            history.append(AIMessage(content=llm_response))
            continue

        elif intent == "visao":
            saudacao = "Oi Nielsen, vou verificar a câmera pra você."
            print(f"🤖: {saudacao}")
            await asyncio.to_thread(speech_agent.speak, saudacao)

            vision_desc = await asyncio.to_thread(vision_agent.capture_and_describe)
            print('📸 Descrição visão:', vision_desc)
            full_prompt = f"{cleaned_input}\nVisão: {vision_desc}"

        else:
            full_prompt = cleaned_input
            saudacao = "Oi Nielsen, vou processar sua solicitação."
            await asyncio.to_thread(speech_agent.speak, saudacao)

        # Envia pro LLM
        history.append(HumanMessage(content=full_prompt))
        modelo_escolhido = modelos_disponiveis[escolha]
        print(f"✅ Modelo selecionado: {modelo_escolhido}")

        llm_response = await asyncio.to_thread(
            cached_llm_response, full_prompt, modelo_escolhido
        )
        print("🤖:", llm_response)

        await asyncio.to_thread(speech_agent.speak, llm_response)
        history.append(AIMessage(content=llm_response))

if __name__ == "__main__":
    asyncio.run(main_async())
