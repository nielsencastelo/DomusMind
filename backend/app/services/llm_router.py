from collections.abc import AsyncGenerator, Iterable

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.core.settings import settings


class LLMRouter:
    """
    Multi-provider LLM router with automatic fallback.
    Runtime provider settings stored in system_config override .env values.
    """

    def __init__(self):
        self.default_chain = [
            p.strip().lower()
            for p in settings.llm_fallback_chain.split(",")
            if p.strip()
        ]

    @staticmethod
    def _normalize(content: object) -> str:
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if text:
                        parts.append(str(text))
                else:
                    parts.append(str(item))
            return "\n".join(parts).strip()
        return str(content).strip()

    @staticmethod
    async def _runtime_config() -> dict:
        try:
            from app.core.database import AsyncSessionLocal
            from app.repositories.config_repo import ConfigRepository

            async with AsyncSessionLocal() as db:
                value = await ConfigRepository(db).get("llm.providers")
            return value if isinstance(value, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _config_value(provider_config: dict, key: str, fallback: str) -> str:
        value = provider_config.get(key) if isinstance(provider_config, dict) else None
        return str(value or fallback)

    def _build(
        self,
        provider: str,
        temperature: float = 0.2,
        model_override: str | None = None,
        runtime_config: dict | None = None,
    ):
        provider_config = runtime_config.get(provider, {}) if runtime_config else {}
        value = lambda key, fallback: self._config_value(provider_config, key, fallback)

        match provider:
            case "local":
                return ChatOllama(
                    model=model_override or value("default_model", settings.local_model),
                    base_url=value("base_url", settings.ollama_base_url),
                    temperature=temperature,
                )
            case "openai":
                api_key = value("api_key", settings.openai_api_key)
                if not api_key:
                    raise RuntimeError("OPENAI_API_KEY nao definido.")
                return ChatOpenAI(
                    model=model_override or value("default_model", settings.openai_model),
                    api_key=api_key,
                    temperature=temperature,
                )
            case "gemini":
                api_key = value("api_key", settings.gemini_api_key)
                if not api_key:
                    raise RuntimeError("GEMINI_API_KEY nao definido.")
                return ChatGoogleGenerativeAI(
                    model=model_override or value("default_model", settings.gemini_model),
                    google_api_key=api_key,
                    temperature=temperature,
                )
            case "claude":
                api_key = value("api_key", settings.anthropic_api_key)
                if not api_key:
                    raise RuntimeError("ANTHROPIC_API_KEY nao definido.")
                return ChatAnthropic(
                    model=model_override or value("default_model", settings.claude_model),
                    api_key=api_key,
                    temperature=temperature,
                )
            case _:
                raise ValueError(f"Provider invalido: {provider}")

    def invoke(
        self,
        messages: list[BaseMessage],
        providers: Iterable[str] | None = None,
        temperature: float = 0.2,
        model_override: str | None = None,
    ) -> tuple[str, str]:
        chain = list(providers) if providers else self.default_chain
        last_error: Exception | None = None

        for provider in chain:
            try:
                model = self._build(provider, temperature, model_override)
                response = model.invoke(messages)
                text = self._normalize(getattr(response, "content", response))
                if not text:
                    raise RuntimeError("Resposta vazia.")
                return text, provider
            except Exception as exc:
                last_error = exc

        raise RuntimeError(f"Nenhum provider respondeu. Ultimo erro: {last_error}")

    async def ainvoke(
        self,
        messages: list[BaseMessage],
        providers: Iterable[str] | None = None,
        temperature: float = 0.2,
        model_override: str | None = None,
    ) -> tuple[str, str]:
        chain = list(providers) if providers else self.default_chain
        last_error: Exception | None = None
        runtime_config = await self._runtime_config()

        for provider in chain:
            try:
                model = self._build(provider, temperature, model_override, runtime_config)
                response = await model.ainvoke(messages)
                text = self._normalize(getattr(response, "content", response))
                if not text:
                    raise RuntimeError("Resposta vazia.")
                return text, provider
            except Exception as exc:
                last_error = exc

        raise RuntimeError(f"Nenhum provider respondeu. Ultimo erro: {last_error}")

    async def astream(
        self,
        messages: list[BaseMessage],
        providers: Iterable[str] | None = None,
        temperature: float = 0.2,
        model_override: str | None = None,
    ) -> AsyncGenerator[tuple[str, str], None]:
        """Yield (token, provider) for streaming responses."""
        chain = list(providers) if providers else self.default_chain
        last_error: Exception | None = None
        runtime_config = await self._runtime_config()

        for provider in chain:
            try:
                model = self._build(provider, temperature, model_override, runtime_config)
                async for chunk in model.astream(messages):
                    text = self._normalize(getattr(chunk, "content", chunk))
                    if text:
                        yield text, provider
                return
            except Exception as exc:
                last_error = exc

        raise RuntimeError(f"Nenhum provider para streaming. Ultimo erro: {last_error}")

    def build_messages(
        self,
        user_input: str,
        system_prompt: str | None = None,
        history: list[dict] | None = None,
    ) -> list[BaseMessage]:
        msgs: list[BaseMessage] = []
        if system_prompt:
            msgs.append(SystemMessage(content=system_prompt))
        for item in history or []:
            role = item.get("role")
            content = item.get("content", "")
            if role == "user":
                msgs.append(HumanMessage(content=content))
            elif role == "assistant":
                msgs.append(AIMessage(content=content))
        msgs.append(HumanMessage(content=user_input))
        return msgs
