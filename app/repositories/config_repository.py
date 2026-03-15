import json
from pathlib import Path
from typing import Any

from app.core.settings import settings


class ConfigRepository:
    def __init__(self, config_path: str | None = None):
        self.config_path = Path(config_path or settings.rooms_config_path)

    def _ensure_parent(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def load_rooms(self) -> dict[str, Any]:
        self._ensure_parent()

        if not self.config_path.exists():
            self.save_rooms({})
            return {}

        with open(self.config_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return {}

        return data

    def save_rooms(self, rooms: dict[str, Any]) -> None:
        self._ensure_parent()
        with open(self.config_path, "w", encoding="utf-8") as file:
            json.dump(rooms, file, indent=2, ensure_ascii=False)