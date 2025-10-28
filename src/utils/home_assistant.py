import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

HASS_URL = os.getenv("HASS_URL", "http://localhost:8123")
TOKEN = os.getenv("TOKEN")
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_FILE = os.path.join(BASE_DIR, "configs", "rooms.json")


def load_room_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def toggle_light(room: str, turn_on: bool = True):
    rooms = load_room_config()

    if room not in rooms:
        return False, f"Cômodo '{room}' não encontrado nas configurações."

    entity_id = rooms[room].get("light_entity_id")
    if not entity_id:
        return False, f"Entity ID da luz não definido para o cômodo '{room}'."

    service = "turn_on" if turn_on else "turn_off"
    url = f"{HASS_URL}/api/services/switch/{service}"
    payload = {"entity_id": entity_id}

    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=5)
        if response.ok:
            return True, f"Luz do '{room}' {'ligada' if turn_on else 'desligada'} com sucesso."
        else:
            return False, f"Erro do HA: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"Erro de conexão: {str(e)}"
