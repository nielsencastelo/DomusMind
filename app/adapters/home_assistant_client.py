import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

HASS_URL = os.getenv("HASS_URL", "http://localhost:8123")
TOKEN = os.getenv("TOKEN")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}


class HomeAssistantClient:
    def __init__(self, config_file: str = "configs/rooms.json"):
        self.config_file = config_file

    def load_room_config(self) -> dict:
        with open(self.config_file, "r", encoding="utf-8") as f:
            return json.load(f)

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
        url = f"{HASS_URL}/api/services/{light_domain}/{service}"
        payload = {"entity_id": entity_id}

        try:
            response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
            if response.ok:
                action_text = "ligada" if turn_on else "desligada"
                return True, f"Luz do '{room}' {action_text} com sucesso."
            return False, f"Erro do Home Assistant: {response.status_code} - {response.text}"
        except Exception as exc:
            return False, f"Erro de conexão com Home Assistant: {exc}"

    def ping(self) -> dict:
        try:
            response = requests.get(f"{HASS_URL}/api/", headers=HEADERS, timeout=10)
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