from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse, SpeechRequest, SimpleMessageResponse
from app.services.orchestrator import DomusOrchestrator
from app.services.speech_service import SpeechService

router = APIRouter()

orchestrator = DomusOrchestrator()
speech_service = SpeechService()


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


@router.post("/speech", response_model=SimpleMessageResponse)
def speak(payload: SpeechRequest):
    try:
        speech_service.speak_text_with_tts(payload.text)
        return SimpleMessageResponse(ok=True, message="Áudio reproduzido com sucesso.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc