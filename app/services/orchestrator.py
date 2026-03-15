from app.prompts.system_prompts import (
    EXIT_RESPONSE_SYSTEM_PROMPT,
    FINAL_RESPONSE_SYSTEM_PROMPT,
    SEARCH_SUMMARY_SYSTEM_PROMPT,
    VISION_RESPONSE_SYSTEM_PROMPT,
)
from app.services.intent_service import IntentService
from app.services.light_service import LightService
from app.services.response_service import ResponseService
from app.services.search_service import SearchService
from app.services.vision_service import VisionService


class DomusOrchestrator:
    """
    Orquestrador principal.
    Substitui o graph_agent.py antigo por uma camada mais simples, modular e orientada a serviços.
    """

    def __init__(self):
        self.intent_service = IntentService()
        self.light_service = LightService()
        self.response_service = ResponseService()
        self.search_service = SearchService()
        self.vision_service = VisionService()

    def handle(self, message: str, history: list[dict] | None = None) -> dict:
        history = history or []
        cleaned = message.strip()
        intent = self.intent_service.classify(cleaned)

        if intent == "visao":
            vision_context = self.vision_service.capture_and_describe()
            response, provider = self.response_service.ask(
                user_input=f"Comando do usuário: {cleaned}\n\nContexto de visão:\n{vision_context}",
                history=history,
                system_prompt=VISION_RESPONSE_SYSTEM_PROMPT,
                providers=["local", "openai", "gemini", "claude"],
                temperature=0.2,
            )

        elif intent == "pesquisa":
            search_context, _ = self.search_service.search_and_summarize(cleaned)
            response, provider = self.response_service.ask(
                user_input=f"Comando do usuário: {cleaned}\n\nResultados de busca:\n{search_context}",
                history=history,
                system_prompt=SEARCH_SUMMARY_SYSTEM_PROMPT,
                providers=["openai", "gemini", "claude", "local"],
                temperature=0.2,
            )

        elif intent == "luz":
            light_result = self.light_service.execute(cleaned)
            response, provider = self.response_service.ask(
                user_input=f"Comando do usuário: {cleaned}\n\nResultado da automação:\n{light_result['message']}",
                history=history,
                system_prompt=FINAL_RESPONSE_SYSTEM_PROMPT,
                providers=["local", "openai", "gemini", "claude"],
                temperature=0.2,
            )

        elif intent == "sair":
            response, provider = self.response_service.ask(
                user_input=cleaned,
                history=history,
                system_prompt=EXIT_RESPONSE_SYSTEM_PROMPT,
                providers=["local", "openai", "gemini", "claude"],
                temperature=0.0,
            )

        else:
            response, provider = self.response_service.ask(
                user_input=cleaned,
                history=history,
                system_prompt=FINAL_RESPONSE_SYSTEM_PROMPT,
                providers=["local", "openai", "gemini", "claude"],
                temperature=0.2,
            )

        new_history = history + [
            {"role": "user", "content": cleaned},
            {"role": "assistant", "content": response},
        ]

        return {
            "intent": intent,
            "response": response,
            "provider_used": provider,
            "history": new_history,
        }