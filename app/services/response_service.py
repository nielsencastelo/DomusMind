from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.services.router_llm import ProviderRouter


class ResponseService:
    def __init__(self):
        self.router = ProviderRouter()

    def _history_to_messages(self, history: list[dict]) -> list[BaseMessage]:
        messages: list[BaseMessage] = []

        for item in history:
            role = item.get("role")
            content = item.get("content", "")

            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

        return messages

    def ask(
        self,
        user_input: str,
        history: list[dict],
        system_prompt: str,
        providers: list[str] | None = None,
        temperature: float = 0.2,
    ) -> tuple[str, str]:
        messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]
        messages.extend(self._history_to_messages(history))
        messages.append(HumanMessage(content=user_input))

        return self.router.invoke_messages(
            messages=messages,
            providers=providers,
            temperature=temperature,
        )