from __future__ import annotations

from typing import TypedDict, List

from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langgraph.graph import StateGraph, END

from agents.audio_agent import AudioAgent
from agents.intent_classifier_agent import IntentClassifierAgent
from agents.light_control_agent import LightControlAgent
from agents.llm_agent import LLMAgent
from agents.prompts import (
    EXIT_RESPONSE_SYSTEM_PROMPT,
    FINAL_RESPONSE_SYSTEM_PROMPT,
    SEARCH_SUMMARY_SYSTEM_PROMPT,
    VISION_RESPONSE_SYSTEM_PROMPT,
)
from agents.search_agent import SearchAgent
from agents.speech_agent import SpeechAgent
from agents.vision_agent import VisionAgent


class DomusState(TypedDict, total=False):
    user_input: str
    cleaned_input: str
    intent: str
    history: List[BaseMessage]

    vision_context: str
    search_context: str
    light_result: str

    response: str
    provider_used: str


class GraphDomusAgent:
    """
    Orquestrador principal com LangGraph.
    """

    def __init__(self):
        self.audio_agent = AudioAgent()
        self.speech_agent = SpeechAgent()
        self.vision_agent = VisionAgent()
        self.search_agent = SearchAgent()
        self.intent_agent = IntentClassifierAgent(providers=["local", "openai", "gemini", "claude"])
        self.light_agent = LightControlAgent(providers=["local", "openai", "gemini", "claude"])
        self.llm_agent = LLMAgent()

        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(DomusState)

        graph.add_node("classify_intent", self._classify_intent)
        graph.add_node("run_vision", self._run_vision)
        graph.add_node("run_search", self._run_search)
        graph.add_node("run_light", self._run_light)
        graph.add_node("respond_exit", self._respond_exit)
        graph.add_node("compose_response", self._compose_response)

        graph.set_entry_point("classify_intent")

        graph.add_conditional_edges(
            "classify_intent",
            self._route_after_intent,
            {
                "visao": "run_vision",
                "pesquisa": "run_search",
                "luz": "run_light",
                "sair": "respond_exit",
                "outro": "compose_response",
            },
        )

        graph.add_edge("run_vision", "compose_response")
        graph.add_edge("run_search", "compose_response")
        graph.add_edge("run_light", "compose_response")
        graph.add_edge("respond_exit", END)
        graph.add_edge("compose_response", END)

        return graph.compile()

    def _classify_intent(self, state: DomusState) -> DomusState:
        cleaned = state["user_input"].strip()
        intent = self.intent_agent.classify(cleaned)
        return {
            "cleaned_input": cleaned,
            "intent": intent,
        }

    def _route_after_intent(self, state: DomusState) -> str:
        return state.get("intent", "outro")

    def _run_vision(self, state: DomusState) -> DomusState:
        vision_desc = self.vision_agent.capture_and_describe()
        return {"vision_context": vision_desc}

    def _run_search(self, state: DomusState) -> DomusState:
        search_text, _file_path = self.search_agent.search_and_summarize(state["cleaned_input"])
        return {"search_context": search_text}

    def _run_light(self, state: DomusState) -> DomusState:
        result = self.light_agent.execute(state["cleaned_input"])
        return {"light_result": result["message"]}

    def _respond_exit(self, state: DomusState) -> DomusState:
        response, provider = self.llm_agent.ask(
            user_input=state["cleaned_input"],
            history=state.get("history", []),
            system_prompt=EXIT_RESPONSE_SYSTEM_PROMPT,
            providers=["local", "openai", "gemini", "claude"],
            temperature=0.0,
        )
        return {
            "response": response,
            "provider_used": provider,
        }

    def _compose_response(self, state: DomusState) -> DomusState:
        blocks = [f"Comando do usuário: {state['cleaned_input']}"]

        if state.get("vision_context"):
            blocks.append(f"Contexto de visão:\n{state['vision_context']}")

        if state.get("search_context"):
            blocks.append(f"Resultados de busca:\n{state['search_context']}")

        if state.get("light_result"):
            blocks.append(f"Resultado da automação:\n{state['light_result']}")

        if state.get("intent") == "pesquisa":
            system_prompt = SEARCH_SUMMARY_SYSTEM_PROMPT
            providers = ["openai", "gemini", "claude", "local"]
        elif state.get("intent") == "visao":
            system_prompt = VISION_RESPONSE_SYSTEM_PROMPT
            providers = ["local", "openai", "gemini", "claude"]
        elif state.get("intent") == "luz":
            system_prompt = FINAL_RESPONSE_SYSTEM_PROMPT
            providers = ["local", "openai", "gemini", "claude"]
        else:
            system_prompt = FINAL_RESPONSE_SYSTEM_PROMPT
            providers = ["local", "openai", "gemini", "claude"]

        prompt = "\n\n".join(blocks)

        response, provider = self.llm_agent.ask(
            user_input=prompt,
            history=state.get("history", []),
            system_prompt=system_prompt,
            providers=providers,
            temperature=0.2,
        )

        return {
            "response": response,
            "provider_used": provider,
        }

    def handle(self, user_input: str, history: list[BaseMessage] | None = None) -> dict:
        history = history or []

        result = self.graph.invoke(
            {
                "user_input": user_input,
                "history": history,
            }
        )

        updated_history = history + [
            HumanMessage(content=user_input),
            AIMessage(content=result["response"]),
        ]

        return {
            "intent": result.get("intent", "outro"),
            "response": result["response"],
            "provider_used": result.get("provider_used", "unknown"),
            "history": updated_history,
        }