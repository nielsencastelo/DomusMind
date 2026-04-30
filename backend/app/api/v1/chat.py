import uuid

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.agents.orchestrator import agent_graph
from app.agents.state import AgentState
from app.core.redis import session_get
from app.models.schemas import (
    AgentTestRequest,
    AgentTestResponse,
    ChatRequest,
    ChatResponse,
    HistoryItem,
    OkResponse,
    SpeechRequest,
    TranscriptionResponse,
)
from app.prompts.system_prompts import (
    FINAL_RESPONSE_SYSTEM_PROMPT,
    INTENT_SYSTEM_PROMPT,
    LIGHT_PARSE_SYSTEM_PROMPT,
    SEARCH_SUMMARY_SYSTEM_PROMPT,
    VISION_RESPONSE_SYSTEM_PROMPT,
)
from app.services.llm_router import LLMRouter

router = APIRouter(prefix="/chat", tags=["chat"])

AGENT_PROMPTS = {
    "geral": FINAL_RESPONSE_SYSTEM_PROMPT,
    "intent": INTENT_SYSTEM_PROMPT,
    "visao": VISION_RESPONSE_SYSTEM_PROMPT,
    "pesquisa": SEARCH_SUMMARY_SYSTEM_PROMPT,
    "luz": LIGHT_PARSE_SYSTEM_PROMPT,
    "memoria": FINAL_RESPONSE_SYSTEM_PROMPT,
}


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    """Process a text message through the LangGraph agent pipeline."""
    initial_state: AgentState = {
        "session_id": payload.session_id,
        "user_input": payload.message,
        "intent": "",
        "vision_context": None,
        "search_results": None,
        "ha_result": None,
        "memory_context": None,
        "short_term_history": [],
        "final_response": None,
        "provider_used": "",
        "error": None,
    }

    try:
        result: AgentState = await agent_graph.ainvoke(initial_state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    history = await session_get(payload.session_id)
    history_items = [HistoryItem(role=h["role"], content=h["content"]) for h in history]

    return ChatResponse(
        session_id=payload.session_id,
        intent=result.get("intent", "outro"),
        response=result.get("final_response", ""),
        provider_used=result.get("provider_used", ""),
        history=history_items,
    )


@router.post("/test-agent", response_model=AgentTestResponse)
async def test_agent(payload: AgentTestRequest):
    router_ = LLMRouter()
    providers = [payload.provider] if payload.provider else None
    system = AGENT_PROMPTS[payload.agent]
    message = payload.message
    if payload.agent == "memoria":
        message = f"Teste de memoria/RAG sem gravar conversa:\n{payload.message}"

    try:
        messages = router_.build_messages(message, system_prompt=system)
        response, provider = await router_.ainvoke(
            messages,
            providers=providers,
            temperature=payload.temperature,
            model_override=payload.model,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return AgentTestResponse(
        agent=payload.agent,
        provider_used=provider,
        response=response,
    )


@router.websocket("/ws/{session_id}")
async def chat_ws(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for streaming LLM responses token-by-token.
    Client sends: {"message": "..."}
    Server sends: {"type": "token"|"done"|"error", "data": "..."}
    """
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "").strip()
            if not message:
                continue

            # Run classification + context gathering (non-streaming part)
            initial_state: AgentState = {
                "session_id": session_id,
                "user_input": message,
                "intent": "",
                "vision_context": None,
                "search_results": None,
                "ha_result": None,
                "memory_context": None,
                "short_term_history": [],
                "final_response": None,
                "provider_used": "",
                "error": None,
            }

            try:
                result: AgentState = await agent_graph.ainvoke(initial_state)
                response_text = result.get("final_response", "")

                # Stream the response word by word to simulate token streaming
                words = response_text.split()
                for i, word in enumerate(words):
                    token = word + (" " if i < len(words) - 1 else "")
                    await websocket.send_json({"type": "token", "data": token})

                await websocket.send_json({
                    "type": "done",
                    "data": {
                        "intent": result.get("intent", ""),
                        "provider": result.get("provider_used", ""),
                    },
                })
            except Exception as exc:
                await websocket.send_json({"type": "error", "data": str(exc)})

    except WebSocketDisconnect:
        pass


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe():
    """Capture microphone audio and return transcription."""
    try:
        from app.services.audio_service import AudioService
        audio = AudioService()
        text = audio.capture_and_transcribe()
        return TranscriptionResponse(ok=True, text=text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/speech", response_model=OkResponse)
async def speak(payload: SpeechRequest):
    """Convert text to speech and play on server speaker."""
    try:
        from app.services.speech_service import SpeechService
        svc = SpeechService()
        svc.speak(payload.text)
        return OkResponse(ok=True, message="Áudio reproduzido com sucesso.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/history/{session_id}")
async def get_history(session_id: str, limit: int = 50):
    """Retrieve conversation history for a session from PostgreSQL."""
    try:
        from app.core.database import AsyncSessionLocal
        from app.repositories.conversation_repo import ConversationRepository

        async with AsyncSessionLocal() as db:
            repo = ConversationRepository(db)
            rows = await repo.get_by_session(session_id, limit=limit)

        return [
            {"role": r.role, "content": r.content, "created_at": r.created_at}
            for r in rows
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
