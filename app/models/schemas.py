from typing import Any, Literal

from pydantic import BaseModel, Field


class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: list[HistoryItem] = Field(default_factory=list)


class ChatResponse(BaseModel):
    intent: str
    response: str
    provider_used: str
    history: list[HistoryItem]


class SpeechRequest(BaseModel):
    text: str = Field(..., min_length=1)


class TranscriptionResponse(BaseModel):
    ok: bool
    text: str


class SimpleMessageResponse(BaseModel):
    ok: bool
    message: str


class LightActionRequest(BaseModel):
    room: str
    action: Literal["on", "off"]


class DeviceActionResponse(BaseModel):
    ok: bool
    message: str


class VisionRequest(BaseModel):
    room: str


class VisionResponse(BaseModel):
    ok: bool
    room: str
    description: str


class RoomsConfigResponse(BaseModel):
    rooms: dict[str, Any]


class RoomsConfigUpdateRequest(BaseModel):
    rooms: dict[str, Any]