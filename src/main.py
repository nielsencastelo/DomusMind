import asyncio

from agents.graph_agent import GraphDomusAgent


WAKE_WORDS = {"coca", "koka", "coka", "kouka", "cuca"}


async def main_async():
    orchestrator = GraphDomusAgent()
    history = []

    while True:
        print("🎤 Aguardando comando com wake word...")
        user_input = await asyncio.to_thread(orchestrator.audio_agent.listen_and_transcribe)

        if not user_input:
            continue

        lowered = user_input.lower().strip()
        if not any(w in lowered for w in WAKE_WORDS):
            continue

        print(f"✅ Comando detectado: {user_input}")

        try:
            result = await asyncio.to_thread(orchestrator.handle, user_input, history)
            history = result["history"]

            response = result["response"]
            provider = result["provider_used"]
            intent = result["intent"]

            print(f"🧠 Intent: {intent}")
            print(f"🤖 Provider: {provider}")
            print(f"💬 Resposta: {response}")

            await asyncio.to_thread(orchestrator.speech_agent.speak, response)

            if intent == "sair":
                return

        except Exception as exc:
            error_msg = f"Desculpe, ocorreu um erro no pipeline de agentes: {exc}"
            print(error_msg)
            await asyncio.to_thread(orchestrator.speech_agent.speak, error_msg)


if __name__ == "__main__":
    asyncio.run(main_async())