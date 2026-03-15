from agents.model_router import ProviderRouter
from agents.prompts import INTENT_SYSTEM_PROMPT


class IntentClassifierAgent:
    """
    Classificador leve de intenção.
    Usa local/Phi-4 por padrão para reduzir custo e latência.
    """

    VALID_INTENTS = {"visao", "pesquisa", "luz", "sair", "outro"}

    def __init__(self, providers: list[str] | None = None):
        self.router = ProviderRouter()
        self.providers = providers or ["local", "openai", "gemini", "claude"]

    def classify(self, transcribed_text: str) -> str:
        try:
            result, _provider = self.router.invoke_text(
                user_text=transcribed_text,
                system_text=INTENT_SYSTEM_PROMPT,
                providers=self.providers,
                temperature=0.0,
            )
            result = result.strip().lower()
            return result if result in self.VALID_INTENTS else "outro"
        except Exception:
            return "outro"