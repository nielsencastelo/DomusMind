from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agents.model_router import ProviderRouter


class LLMAgent:
    """
    Agente genérico de resposta usando um router multi-provider.
    """

    def __init__(self):
        self.router = ProviderRouter()

    def ask(
        self,
        user_input: str,
        history: list | None = None,
        system_prompt: str | None = None,
        providers: list[str] | None = None,
        temperature: float = 0.2,
    ) -> tuple[str, str]:
        messages = []

        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        history = history or []
        for msg in history[-8:]:
            if isinstance(msg, HumanMessage):
                messages.append(msg)
            elif isinstance(msg, AIMessage):
                messages.append(msg)

        messages.append(HumanMessage(content=user_input))
        return self.router.invoke_messages(
            messages=messages,
            providers=providers,
            temperature=temperature,
        )