from app.prompts.system_prompts import INTENT_SYSTEM_PROMPT
from app.services.router_llm import ProviderRouter


class IntentService:
    def __init__(self, providers: list[str] | None = None):
        self.router = ProviderRouter()
        self.providers = providers or ["local", "openai", "gemini", "claude"]

    def classify(self, text: str) -> str:
        response, _provider = self.router.invoke_text(
            user_text=text,
            system_text=INTENT_SYSTEM_PROMPT,
            providers=self.providers,
            temperature=0.0,
        )

        intent = response.strip().lower()
        valid = {"visao", "pesquisa", "luz", "sair", "outro"}

        if intent not in valid:
            return "outro"

        return intent