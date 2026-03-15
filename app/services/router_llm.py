from typing import Iterable

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.core.settings import settings


class ProviderRouter:
    """
    Roteador central de LLMs.
    Prioriza o provider solicitado e faz fallback automaticamente.
    """

    def __init__(self):
        self.local_model = settings.local_model
        self.openai_model = settings.openai_model
        self.gemini_model = settings.gemini_model
        self.claude_model = settings.claude_model
        self.default_chain = self._parse_chain(settings.llm_fallback_chain)

    @staticmethod
    def _parse_chain(raw: str) -> list[str]:
        return [item.strip().lower() for item in raw.split(",") if item.strip()]

    @staticmethod
    def _normalize_content(content) -> str:
        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if text:
                        parts.append(str(text))
                else:
                    parts.append(str(item))
            return "\n".join(parts).strip()

        return str(content).strip()

    def _build_model(self, provider: str, temperature: float = 0.2):
        provider = provider.lower()

        if provider == "local":
            return ChatOllama(model=self.local_model, temperature=temperature)

        if provider == "openai":
            if not self.openai_model:
                raise RuntimeError("OPENAI_MODEL não definido.")
            return ChatOpenAI(model=self.openai_model, temperature=temperature)

        if provider == "gemini":
            if not self.gemini_model:
                raise RuntimeError("GEMINI_MODEL não definido.")
            return ChatGoogleGenerativeAI(model=self.gemini_model, temperature=temperature)

        if provider == "claude":
            if not self.claude_model:
                raise RuntimeError("CLAUDE_MODEL não definido.")
            return ChatAnthropic(model=self.claude_model, temperature=temperature)

        raise ValueError(f"Provider inválido: {provider}")

    def invoke_messages(
        self,
        messages: list[BaseMessage],
        providers: Iterable[str] | None = None,
        temperature: float = 0.2,
    ) -> tuple[str, str]:
        tried: list[str] = []
        last_error: Exception | None = None
        chain = list(providers) if providers else self.default_chain

        for provider in chain:
            try:
                model = self._build_model(provider=provider, temperature=temperature)
                response = model.invoke(messages)
                text = self._normalize_content(getattr(response, "content", response))

                if not text:
                    raise RuntimeError("Resposta vazia do modelo.")

                return text, provider
            except Exception as exc:
                tried.append(provider)
                last_error = exc

        raise RuntimeError(
            f"Nenhum provider respondeu com sucesso. Tentados: {tried}. Último erro: {last_error}"
        )

    def invoke_text(
        self,
        user_text: str,
        system_text: str | None = None,
        providers: Iterable[str] | None = None,
        temperature: float = 0.2,
    ) -> tuple[str, str]:
        messages: list[BaseMessage] = []

        if system_text:
            messages.append(SystemMessage(content=system_text))

        messages.append(HumanMessage(content=user_text))

        return self.invoke_messages(
            messages=messages,
            providers=providers,
            temperature=temperature,
        )