import json
import re

from app.adapters.home_assistant_client import HomeAssistantClient
from app.prompts.system_prompts import LIGHT_PARSE_SYSTEM_PROMPT
from app.services.router_llm import ProviderRouter


class LightService:
    def __init__(self, providers: list[str] | None = None):
        self.router = ProviderRouter()
        self.ha_client = HomeAssistantClient()
        self.providers = providers or ["local", "openai", "gemini", "claude"]

    @staticmethod
    def _extract_json(text: str) -> dict:
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return {"room": "", "action": "unknown"}

            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return {"room": "", "action": "unknown"}

    def parse_command(self, command: str) -> dict:
        response, _provider = self.router.invoke_text(
            user_text=command,
            system_text=LIGHT_PARSE_SYSTEM_PROMPT,
            providers=self.providers,
            temperature=0.0,
        )

        parsed = self._extract_json(response)
        room = str(parsed.get("room", "")).strip().lower()
        action = str(parsed.get("action", "unknown")).strip().lower()

        if action not in {"on", "off"}:
            action = "unknown"

        return {"room": room, "action": action}

    def execute(self, command: str) -> dict:
        parsed = self.parse_command(command)
        room = parsed["room"]
        action = parsed["action"]

        if not room:
            return {"ok": False, "message": "Não consegui identificar o cômodo.", "parsed": parsed}

        if action == "unknown":
            return {
                "ok": False,
                "message": "Não consegui identificar se era para ligar ou desligar.",
                "parsed": parsed,
            }

        ok, message = self.ha_client.toggle_light(room=room, turn_on=(action == "on"))
        return {"ok": ok, "message": message, "parsed": parsed}