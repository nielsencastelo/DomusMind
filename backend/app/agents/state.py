from typing import TypedDict


class AgentState(TypedDict):
    # Input
    session_id: str
    user_input: str

    # Routing
    intent: str  # visao | pesquisa | luz | sair | outro

    # Context gathered by specialized agents
    vision_context: str | None
    search_results: str | None
    ha_result: str | None
    memory_context: str | None

    # Short-term context from Redis (list of {role, content})
    short_term_history: list[dict]

    # Output
    final_response: str | None
    provider_used: str

    # Optional error propagation
    error: str | None
