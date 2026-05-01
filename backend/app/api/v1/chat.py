import uuid
import tempfile
import wave
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import agent_graph
from app.agents.state import AgentState
from app.core.database import get_db
from app.core.redis import session_get
from app.core.settings import settings
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


class AudioConfigOut(BaseModel):
    audio_sample_rate: int
    whisper_model: str
    whisper_compute_type: str
    tts_model_name: str
    tts_speaker_wav: str
    tts_language: str
    tts_voice_ready: bool


class AudioConfigIn(BaseModel):
    audio_sample_rate: int | None = None
    whisper_model: str | None = None
    whisper_compute_type: str | None = None
    tts_model_name: str | None = None
    tts_speaker_wav: str | None = None
    tts_language: str | None = None


async def _audio_config(db: AsyncSession) -> AudioConfigOut:
    from app.repositories.config_repo import ConfigRepository

    repo = ConfigRepository(db)
    sample_rate = await repo.get("audio.sample_rate")
    whisper_model = await repo.get("audio.whisper_model")
    whisper_compute_type = await repo.get("audio.whisper_compute_type")
    tts_model_name = await repo.get("audio.tts_model_name")
    tts_speaker_wav = await repo.get("audio.tts_speaker_wav")
    tts_language = await repo.get("audio.tts_language")
    speaker_wav = str(tts_speaker_wav or settings.tts_speaker_wav)

    return AudioConfigOut(
        audio_sample_rate=int(sample_rate) if sample_rate is not None else settings.audio_sample_rate,
        whisper_model=str(whisper_model or settings.whisper_model),
        whisper_compute_type=str(whisper_compute_type or settings.whisper_compute_type),
        tts_model_name=str(tts_model_name or settings.tts_model_name),
        tts_speaker_wav=speaker_wav,
        tts_language=str(tts_language or settings.tts_language),
        tts_voice_ready=Path(speaker_wav).exists(),
    )


def _wav_response(pcm: bytes, sample_rate: int) -> Response:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm)
    return Response(content=buffer.getvalue(), media_type="audio/wav")


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


@router.post("/transcribe-file", response_model=TranscriptionResponse)
async def transcribe_file(
    file: UploadFile = File(...),
    language: str = Form("pt"),
    db: AsyncSession = Depends(get_db),
):
    """Transcribe audio recorded in the browser."""
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    tmp_path = ""
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=422, detail="Arquivo de audio vazio.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        from app.services.audio_service import AudioService

        cfg = await _audio_config(db)
        audio = AudioService(
            sample_rate=cfg.audio_sample_rate,
            model_name=cfg.whisper_model,
            compute_type=cfg.whisper_compute_type,
        )
        text = audio.transcribe_file(tmp_path, language=language)
        return TranscriptionResponse(ok=True, text=text)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)


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


@router.post("/speech-audio")
async def speech_audio(payload: SpeechRequest, db: AsyncSession = Depends(get_db)):
    """Convert text to a WAV response for browser playback."""
    try:
        from app.services.speech_service import SpeechService

        cfg = await _audio_config(db)
        svc = SpeechService(
            model_name=cfg.tts_model_name,
            speaker_wav=cfg.tts_speaker_wav,
            language=cfg.tts_language,
        )
        pcm, sample_rate = svc.synthesize_to_bytes(payload.text)
        return _wav_response(pcm, sample_rate)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/audio/config", response_model=AudioConfigOut)
async def get_audio_config(db: AsyncSession = Depends(get_db)):
    return await _audio_config(db)


@router.post("/audio/config", response_model=AudioConfigOut)
async def set_audio_config(payload: AudioConfigIn, db: AsyncSession = Depends(get_db)):
    from app.repositories.config_repo import ConfigRepository

    repo = ConfigRepository(db)
    if payload.audio_sample_rate is not None:
        await repo.set("audio.sample_rate", payload.audio_sample_rate, "Taxa de amostragem do audio")
    if payload.whisper_model is not None:
        await repo.set("audio.whisper_model", payload.whisper_model, "Modelo faster-whisper")
    if payload.whisper_compute_type is not None:
        await repo.set("audio.whisper_compute_type", payload.whisper_compute_type, "Compute type do Whisper")
    if payload.tts_model_name is not None:
        await repo.set("audio.tts_model_name", payload.tts_model_name, "Modelo TTS")
    if payload.tts_speaker_wav is not None:
        await repo.set("audio.tts_speaker_wav", payload.tts_speaker_wav, "Audio de referencia da voz")
    if payload.tts_language is not None:
        await repo.set("audio.tts_language", payload.tts_language, "Idioma do TTS")
    return await _audio_config(db)


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
