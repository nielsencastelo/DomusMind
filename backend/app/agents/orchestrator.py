"""
DomusMind LangGraph orchestrator.

Graph flow:
  classify_intent
       │
  ┌────┴────────────────────────────┐
  │                                 │
  visao   pesquisa   luz   sair    outro
  │       │          │     │        │
  run_vision  run_search  run_ha  (direct)  │
  └───────────────────────────────►fetch_memory
                                   │
                               generate_response
                                   │
                           persist_conversation
                                   │
                                  END
"""

import json
import re

from langgraph.graph import END, StateGraph

from app.agents.state import AgentState
from app.prompts.system_prompts import (
    EXIT_RESPONSE_SYSTEM_PROMPT,
    FINAL_RESPONSE_SYSTEM_PROMPT,
    INTENT_SYSTEM_PROMPT,
    LIGHT_PARSE_SYSTEM_PROMPT,
    SEARCH_SUMMARY_SYSTEM_PROMPT,
    VISION_RESPONSE_SYSTEM_PROMPT,
)
from app.core.redis import session_get, session_append
from app.services.llm_router import LLMRouter
from app.services.search_service import SearchService
from app.services.vision_service import VisionService

_router = LLMRouter()
_search = SearchService()
_vision = VisionService()


async def _agent_llm_options(agent: str) -> dict:
    try:
        from app.core.database import AsyncSessionLocal
        from app.repositories.config_repo import ConfigRepository

        async with AsyncSessionLocal() as db:
            config = await ConfigRepository(db).get("llm.agents")
        if not isinstance(config, dict):
            return {}
        value = config.get(agent) or config.get("geral") or {}
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _providers_from_options(options: dict) -> list[str] | None:
    provider = str(options.get("provider") or "").strip().lower()
    fallback = options.get("fallback")
    providers = []
    if provider:
        providers.append(provider)
    if isinstance(fallback, list):
        providers.extend(str(item).strip().lower() for item in fallback if str(item).strip())
    return providers or None


# ── Node helpers ───────────────────────────────────────────────────────────────

async def _classify_intent(state: AgentState) -> AgentState:
    text = state["user_input"]
    messages = _router.build_messages(text, system_prompt=INTENT_SYSTEM_PROMPT)
    options = await _agent_llm_options("intent")
    response, _ = await _router.ainvoke(
        messages,
        providers=_providers_from_options(options),
        temperature=0.0,
        model_override=options.get("model"),
    )
    intent = response.strip().lower()
    valid = {"visao", "pesquisa", "luz", "sair", "outro"}
    state["intent"] = intent if intent in valid else "outro"
    return state


def _route_intent(state: AgentState) -> str:
    return state.get("intent", "outro")


_CAMERA_EXTRACT_PROMPT = (
    "Extract the camera name from the user's message. "
    "Return only the camera name (e.g. 'sala', 'garagem', 'entrada') or empty string if not specified. "
    "No explanations."
)


async def _run_vision(state: AgentState) -> AgentState:
    camera_name: str | None = None
    try:
        msgs = _router.build_messages(state["user_input"], system_prompt=_CAMERA_EXTRACT_PROMPT)
        raw, _ = await _router.ainvoke(msgs, temperature=0.0)
        extracted = raw.strip().lower()
        if extracted and extracted not in {"", "none", "null"}:
            camera_name = extracted
    except Exception:
        pass

    try:
        description = await _vision.describe(camera_name=camera_name)
        state["vision_context"] = description
    except Exception as exc:
        state["vision_context"] = f"Erro ao acessar câmera: {exc}"
    return state


async def _run_search(state: AgentState) -> AgentState:
    try:
        state["search_results"] = _search.search_and_format(state["user_input"])
    except Exception as exc:
        state["search_results"] = f"Erro na busca: {exc}"
    return state


async def _run_ha(state: AgentState) -> AgentState:
    """Parse light command and execute via Home Assistant."""
    from app.services.ha_service import HAService
    from app.core.database import AsyncSessionLocal
    from app.repositories.room_repo import RoomRepository

    command = state["user_input"]
    messages = _router.build_messages(command, system_prompt=LIGHT_PARSE_SYSTEM_PROMPT)

    try:
        raw, _ = await _router.ainvoke(messages, temperature=0.0)

        raw = raw.strip()
        if not raw.startswith("{"):
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            raw = match.group(0) if match else "{}"

        parsed = json.loads(raw)
        room_name = str(parsed.get("room", "")).strip().lower()
        action = str(parsed.get("action", "unknown")).strip().lower()

        if not room_name or action not in {"on", "off"}:
            state["ha_result"] = "Não consegui identificar o cômodo ou a ação."
            return state

        async with AsyncSessionLocal() as db:
            repo = RoomRepository(db)
            light = await repo.get_light_entity(room_name)

        if not light:
            state["ha_result"] = f"Cômodo '{room_name}' não encontrado."
            return state

        entity_id, domain = light
        ha = HAService()
        ok, msg = await ha.toggle_light(entity_id, domain, turn_on=(action == "on"))
        state["ha_result"] = msg
    except Exception as exc:
        state["ha_result"] = f"Erro ao controlar dispositivo: {exc}"

    return state


async def _fetch_memory(state: AgentState) -> AgentState:
    """Load short-term history from Redis and relevant RAG memories."""
    try:
        history = await session_get(state["session_id"])
        state["short_term_history"] = history
    except Exception:
        state["short_term_history"] = []

    try:
        from app.services.rag_service import RAGService
        from app.core.database import AsyncSessionLocal
        from app.repositories.memory_repo import MemoryRepository

        rag = RAGService()
        embedding = await rag.embed(state["user_input"])
        if embedding:
            async with AsyncSessionLocal() as db:
                repo = MemoryRepository(db)
                chunks = await repo.combined_search(embedding, limit=4)
            if chunks:
                state["memory_context"] = rag.format_context(chunks)
    except Exception:
        pass  # memory is best-effort

    return state


async def _generate_response(state: AgentState) -> AgentState:
    intent = state.get("intent", "outro")

    if intent == "visao":
        context = state.get("vision_context", "")
        user_msg = f"Comando: {state['user_input']}\n\nContexto de visão:\n{context}"
        system = VISION_RESPONSE_SYSTEM_PROMPT
    elif intent == "pesquisa":
        context = state.get("search_results", "")
        user_msg = f"Comando: {state['user_input']}\n\nResultados:\n{context}"
        system = SEARCH_SUMMARY_SYSTEM_PROMPT
    elif intent == "luz":
        result = state.get("ha_result", "")
        user_msg = f"Comando: {state['user_input']}\n\nResultado da automação:\n{result}"
        system = FINAL_RESPONSE_SYSTEM_PROMPT
    elif intent == "sair":
        user_msg = state["user_input"]
        system = EXIT_RESPONSE_SYSTEM_PROMPT
    else:
        user_msg = state["user_input"]
        system = FINAL_RESPONSE_SYSTEM_PROMPT

    # Prepend RAG context to system prompt if available
    memory_context = state.get("memory_context")
    if memory_context:
        system = f"{system}\n\n{memory_context}"

    history = state.get("short_term_history", [])
    messages = _router.build_messages(user_msg, system_prompt=system, history=history)

    try:
        options = await _agent_llm_options(intent if intent != "outro" else "geral")
        response, provider = await _router.ainvoke(
            messages,
            providers=_providers_from_options(options),
            temperature=float(options.get("temperature", 0.2)),
            model_override=options.get("model"),
        )
        state["final_response"] = response
        state["provider_used"] = provider
    except Exception as exc:
        state["final_response"] = "Desculpe, não consegui processar sua solicitação."
        state["provider_used"] = "none"
        state["error"] = str(exc)

    return state


async def _persist_conversation(state: AgentState) -> AgentState:
    """Save turn to Redis (session) and PostgreSQL (long-term)."""
    session_id = state["session_id"]
    user_input = state["user_input"]
    response = state.get("final_response", "")

    try:
        await session_append(session_id, "user", user_input)
        await session_append(session_id, "assistant", response)
    except Exception:
        pass

    try:
        from app.core.database import AsyncSessionLocal
        from app.repositories.conversation_repo import ConversationRepository

        async with AsyncSessionLocal() as db:
            repo = ConversationRepository(db)
            await repo.save(session_id, "user", user_input)
            await repo.save(
                session_id,
                "assistant",
                response,
                intent=state.get("intent"),
                provider=state.get("provider_used"),
            )
    except Exception:
        pass

    return state


# ── Build the graph ────────────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("classify_intent", _classify_intent)
    graph.add_node("run_vision", _run_vision)
    graph.add_node("run_search", _run_search)
    graph.add_node("run_ha", _run_ha)
    graph.add_node("fetch_memory", _fetch_memory)
    graph.add_node("generate_response", _generate_response)
    graph.add_node("persist_conversation", _persist_conversation)

    graph.set_entry_point("classify_intent")

    graph.add_conditional_edges(
        "classify_intent",
        _route_intent,
        {
            "visao": "run_vision",
            "pesquisa": "run_search",
            "luz": "run_ha",
            "sair": "fetch_memory",
            "outro": "fetch_memory",
        },
    )

    graph.add_edge("run_vision", "fetch_memory")
    graph.add_edge("run_search", "fetch_memory")
    graph.add_edge("run_ha", "fetch_memory")
    graph.add_edge("fetch_memory", "generate_response")
    graph.add_edge("generate_response", "persist_conversation")
    graph.add_edge("persist_conversation", END)

    return graph.compile()


# Singleton compiled graph — imported by API layer
agent_graph = build_graph()
