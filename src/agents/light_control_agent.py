import json

from agents.model_router import ProviderRouter
from agents.prompts import LIGHT_PARSE_SYSTEM_PROMPT
from utils.home_assistant import toggle_light


class LightControlAgent:
    """
    Mantém a parte IoT intacta, mudando só a interpretação do comando.
    """

    def __init__(self, providers: list[str] | None = None):
        self.router = ProviderRouter()
        self.providers = providers or ["local", "openai", "gemini", "claude"]

    def parse_command(self, user_text: str) -> dict:
        raw, provider = self.router.invoke_text(
            user_text=user_text,
            system_text=LIGHT_PARSE_SYSTEM_PROMPT,
            providers=self.providers,
            temperature=0.0,
        )

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"room": "", "action": "unknown"}

        data["provider"] = provider
        return data

    def execute(self, user_text: str) -> dict:
        parsed = self.parse_command(user_text)
        room = (parsed.get("room") or "").strip().lower()
        action = (parsed.get("action") or "").strip().lower()

        if not room:
            return {
                "ok": False,
                "message": "Não consegui identificar o cômodo da luz.",
                "room": room,
                "action": action,
                "provider": parsed.get("provider"),
            }

        if action not in {"on", "off"}:
            return {
                "ok": False,
                "message": "Não consegui identificar se era para ligar ou desligar a luz.",
                "room": room,
                "action": action,
                "provider": parsed.get("provider"),
            }

        ok, message = toggle_light(room=room, turn_on=(action == "on"))
        return {
            "ok": ok,
            "message": message,
            "room": room,
            "action": action,
            "provider": parsed.get("provider"),
        }