from typing import Any

import requests

from app.core.settings import settings
from app.repositories.config_repository import ConfigRepository


class HomeAssistantClient:
    def __init__(self, config_file: str | None = None):
        self.base_url = settings.hass_url.rstrip("/")
        self.token = settings.hass_token
        self.config_repo = ConfigRepository(config_path=config_file)

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def load_room_config(self) -> dict[str, Any]:
        return self.config_repo.load_rooms()

    def toggle_light(self, room: str, turn_on: bool = True) -> tuple[bool, str]:
        rooms = self.load_room_config()

        if room not in rooms:
            return False, f"Cômodo '{room}' não encontrado nas configurações."

        room_cfg = rooms[room]
        entity_id = room_cfg.get("light_entity_id")
        light_domain = room_cfg.get("light_domain", "switch")

        if not entity_id:
            return False, f"Entity ID da luz não definido para o cômodo '{room}'."

        service = "turn_on" if turn_on else "turn_off"
        url = f"{self.base_url}/api/services/{light_domain}/{service}"
        payload = {"entity_id": entity_id}

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            if response.ok:
                action_text = "ligada" if turn_on else "desligada"
                return True, f"Luz do '{room}' {action_text} com sucesso."
            return False, f"Erro do Home Assistant: {response.status_code} - {response.text}"
        except Exception as exc:
            return False, f"Erro de conexão com Home Assistant: {exc}"

    def ping(self) -> dict[str, Any]:
        try:
            response = requests.get(f"{self.base_url}/api/", headers=self.headers, timeout=10)
            return {
                "ok": response.ok,
                "status_code": response.status_code,
                "message": "Home Assistant acessível" if response.ok else response.text,
            }
        except Exception as exc:
            return {
                "ok": False,
                "status_code": None,
                "message": str(exc),
            }