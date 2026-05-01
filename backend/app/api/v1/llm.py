from typing import Any, Literal

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.settings import settings
from app.repositories.config_repo import ConfigRepository
from app.services.llm_router import LLMRouter

router = APIRouter(prefix="/llm", tags=["llm"])

Provider = Literal["local", "gemini", "openai", "claude"]


class ProviderConfig(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    default_model: str | None = None


class AgentConfig(BaseModel):
    provider: Provider
    model: str
    temperature: float = 0.2
    fallback: list[Provider] = []


class EmbeddingConfig(BaseModel):
    provider: Literal["local", "google"] = "local"
    model: str = "nomic-embed-text"


class LLMConfig(BaseModel):
    providers: dict[str, ProviderConfig]
    agents: dict[str, AgentConfig]
    embedding: EmbeddingConfig


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    details: dict[str, Any] = {}


class ModelsResponse(BaseModel):
    ok: bool
    provider: str
    models: list[ModelInfo] = []
    message: str = ""


class LLMTestRequest(BaseModel):
    provider: Provider
    model: str
    message: str
    temperature: float = 0.2


class LLMTestResponse(BaseModel):
    ok: bool
    provider_used: str | None = None
    response: str | None = None
    error: str | None = None


DEFAULT_AGENTS: dict[str, AgentConfig] = {
    "geral": AgentConfig(provider="gemini", model=settings.gemini_model, fallback=["local", "openai", "claude"]),
    "intent": AgentConfig(provider="local", model=settings.local_model, temperature=0.0, fallback=["gemini"]),
    "visao": AgentConfig(provider="gemini", model=settings.gemini_model, fallback=["local", "openai"]),
    "pesquisa": AgentConfig(provider="gemini", model=settings.gemini_model, fallback=["local", "openai"]),
    "luz": AgentConfig(provider="local", model=settings.local_model, temperature=0.0, fallback=["gemini"]),
    "memoria": AgentConfig(provider="gemini", model=settings.gemini_model, fallback=["local", "openai"]),
}


def _default_providers() -> dict[str, ProviderConfig]:
    return {
        "local": ProviderConfig(base_url=settings.ollama_base_url, default_model=settings.local_model),
        "gemini": ProviderConfig(api_key=settings.gemini_api_key or None, default_model=settings.gemini_model),
        "openai": ProviderConfig(api_key=settings.openai_api_key or None, default_model=settings.openai_model),
        "claude": ProviderConfig(api_key=settings.anthropic_api_key or None, default_model=settings.claude_model),
    }


async def _load_config(db: AsyncSession) -> LLMConfig:
    repo = ConfigRepository(db)
    providers_raw = await repo.get("llm.providers")
    agents_raw = await repo.get("llm.agents")
    embedding_raw = await repo.get("embedding.config")

    providers = _default_providers()
    if isinstance(providers_raw, dict):
        for key, value in providers_raw.items():
            if isinstance(value, dict) and key in providers:
                providers[key] = ProviderConfig(**{**providers[key].model_dump(), **value})

    agents = dict(DEFAULT_AGENTS)
    if isinstance(agents_raw, dict):
        for key, value in agents_raw.items():
            if isinstance(value, dict):
                agents[key] = AgentConfig(**{**agents.get(key, DEFAULT_AGENTS["geral"]).model_dump(), **value})

    embedding = EmbeddingConfig()
    if isinstance(embedding_raw, dict):
        embedding = EmbeddingConfig(**{**embedding.model_dump(), **embedding_raw})
    else:
        legacy_provider = await repo.get("embedding.provider")
        legacy_model = await repo.get("embedding.model")
        if legacy_provider or legacy_model:
            embedding = EmbeddingConfig(
                provider=legacy_provider or embedding.provider,
                model=legacy_model or embedding.model,
            )

    return LLMConfig(providers=providers, agents=agents, embedding=embedding)


@router.get("/config", response_model=LLMConfig)
async def get_llm_config(db: AsyncSession = Depends(get_db)):
    return await _load_config(db)


@router.post("/config", response_model=LLMConfig)
async def set_llm_config(payload: LLMConfig, db: AsyncSession = Depends(get_db)):
    repo = ConfigRepository(db)
    await repo.set(
        "llm.providers",
        {k: v.model_dump(exclude_none=True) for k, v in payload.providers.items()},
        "Credenciais, base URLs e modelos padrao dos provedores de IA.",
    )
    await repo.set(
        "llm.agents",
        {k: v.model_dump() for k, v in payload.agents.items()},
        "Provider, modelo, temperatura e fallback por agente.",
    )
    await repo.set(
        "embedding.config",
        payload.embedding.model_dump(),
        "Provider e modelo de embeddings.",
    )
    await repo.set("embedding.provider", payload.embedding.provider, "Provider de embeddings.")
    await repo.set("embedding.model", payload.embedding.model, "Modelo de embeddings.")
    return await _load_config(db)


@router.get("/models/{provider}", response_model=ModelsResponse)
async def list_models(provider: Provider, db: AsyncSession = Depends(get_db)):
    cfg = await _load_config(db)
    provider_cfg = cfg.providers.get(provider, ProviderConfig())

    try:
        if provider == "local":
            base_url = (provider_cfg.base_url or settings.ollama_base_url).rstrip("/")
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{base_url}/api/tags")
            response.raise_for_status()
            models = [
                ModelInfo(
                    id=item.get("name", ""),
                    name=item.get("name", ""),
                    provider=provider,
                    details={k: v for k, v in item.items() if k != "name"},
                )
                for item in response.json().get("models", [])
                if item.get("name")
            ]
            return ModelsResponse(ok=True, provider=provider, models=models)

        if provider == "openai":
            if not provider_cfg.api_key:
                return ModelsResponse(ok=False, provider=provider, message="OPENAI_API_KEY nao configurada.")
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {provider_cfg.api_key}"},
                )
            response.raise_for_status()
            models = [
                ModelInfo(id=item["id"], name=item["id"], provider=provider, details=item)
                for item in response.json().get("data", [])
                if item.get("id")
            ]
            models.sort(key=lambda item: item.id)
            return ModelsResponse(ok=True, provider=provider, models=models)

        if provider == "claude":
            if not provider_cfg.api_key:
                return ModelsResponse(ok=False, provider=provider, message="ANTHROPIC_API_KEY nao configurada.")
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(
                    "https://api.anthropic.com/v1/models",
                    headers={
                        "x-api-key": provider_cfg.api_key,
                        "anthropic-version": "2023-06-01",
                    },
                )
            response.raise_for_status()
            models = [
                ModelInfo(
                    id=item["id"],
                    name=item.get("display_name") or item["id"],
                    provider=provider,
                    details=item,
                )
                for item in response.json().get("data", [])
                if item.get("id")
            ]
            return ModelsResponse(ok=True, provider=provider, models=models)

        if provider == "gemini":
            if not provider_cfg.api_key:
                return ModelsResponse(ok=False, provider=provider, message="GEMINI_API_KEY nao configurada.")
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.get(
                    "https://generativelanguage.googleapis.com/v1beta/models",
                    params={"key": provider_cfg.api_key, "pageSize": 1000},
                )
            response.raise_for_status()
            models = []
            for item in response.json().get("models", []):
                name = item.get("name", "").removeprefix("models/")
                methods = item.get("supportedGenerationMethods", [])
                if name and "generateContent" in methods:
                    models.append(ModelInfo(id=name, name=item.get("displayName") or name, provider=provider, details=item))
            return ModelsResponse(ok=True, provider=provider, models=models)

    except Exception as exc:
        return ModelsResponse(ok=False, provider=provider, message=str(exc))

    return ModelsResponse(ok=False, provider=provider, message="Provider invalido.")


@router.post("/test", response_model=LLMTestResponse)
async def test_llm(payload: LLMTestRequest):
    router_ = LLMRouter()
    try:
        messages = router_.build_messages(
            payload.message,
            system_prompt="Responda de forma curta, direta e em portugues do Brasil.",
        )
        response, provider = await router_.ainvoke(
            messages,
            providers=[payload.provider],
            temperature=payload.temperature,
            model_override=payload.model,
        )
        return LLMTestResponse(ok=True, provider_used=provider, response=response)
    except Exception as exc:
        return LLMTestResponse(ok=False, error=str(exc))
