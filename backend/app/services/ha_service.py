from typing import Any

import httpx

from app.core.settings import settings


class HAService:
    """Async Home Assistant REST client."""

    def __init__(self):
        self.base_url = settings.hass_url.rstrip("/")
        self.token = settings.hass_token

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def ping(self) -> dict[str, Any]:
        if not self.token:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    r = await client.get(self.base_url)
                return {
                    "ok": r.status_code < 500,
                    "status_code": r.status_code,
                    "message": (
                        "Home Assistant acessivel. Configure HASS_TOKEN para automacoes."
                        if r.status_code < 500
                        else r.text
                    ),
                }
            except Exception as exc:
                return {"ok": False, "status_code": None, "message": str(exc)}

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{self.base_url}/api/", headers=self._headers
                )
            if r.status_code == 401:
                return {
                    "ok": False,
                    "status_code": r.status_code,
                    "message": "Home Assistant acessivel, mas HASS_TOKEN esta ausente ou invalido.",
                }
            return {
                "ok": r.is_success,
                "status_code": r.status_code,
                "message": "Home Assistant acessível" if r.is_success else r.text,
            }
        except Exception as exc:
            return {"ok": False, "status_code": None, "message": str(exc)}

    async def call_service(
        self,
        domain: str,
        service: str,
        entity_id: str,
        extra: dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        payload: dict[str, Any] = {"entity_id": entity_id}
        if extra:
            payload.update(extra)
        url = f"{self.base_url}/api/services/{domain}/{service}"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(url, headers=self._headers, json=payload)
            if r.is_success:
                return True, "Serviço executado com sucesso."
            return False, f"Erro HA: {r.status_code} — {r.text}"
        except Exception as exc:
            return False, f"Erro de conexão com HA: {exc}"

    async def toggle_light(
        self, entity_id: str, domain: str, turn_on: bool
    ) -> tuple[bool, str]:
        service = "turn_on" if turn_on else "turn_off"
        ok, msg = await self.call_service(domain, service, entity_id)
        if ok:
            action = "ligada" if turn_on else "desligada"
            return True, f"Dispositivo {action} com sucesso."
        return False, msg

    async def get_state(self, entity_id: str) -> dict[str, Any] | None:
        url = f"{self.base_url}/api/states/{entity_id}"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(url, headers=self._headers)
            if r.is_success:
                return r.json()
            return None
        except Exception:
            return None

    async def get_all_states(self) -> list[dict[str, Any]]:
        url = f"{self.base_url}/api/states"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(url, headers=self._headers)
            if r.is_success:
                return r.json()
            return []
        except Exception:
            return []
