from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    SimpleMessageResponse,
    SpeechRequest,
    TranscriptionResponse,
)
from app.services.audio_service import AudioService
from app.services.orchestrator import DomusOrchestrator
from app.services.speech_service import SpeechService

router = APIRouter()

orchestrator = DomusOrchestrator()
speech_service = SpeechService()
audio_service = AudioService()


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    try:
        result = orchestrator.handle(
            message=payload.message,
            history=[item.model_dump() for item in payload.history],
        )
        return ChatResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/chat/speech", response_model=SimpleMessageResponse)
def speak(payload: SpeechRequest):
    try:
        speech_service.speak_text_with_tts(payload.text)
        return SimpleMessageResponse(ok=True, message="Áudio reproduzido com sucesso.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/chat/transcribe", response_model=TranscriptionResponse)
def transcribe():
    try:
        text = audio_service.capture_audio_and_transcribe_continuous()
        return TranscriptionResponse(ok=True, text=text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc