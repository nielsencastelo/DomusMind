import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ── Common ─────────────────────────────────────────────────────────────────────

class OkResponse(BaseModel):
    ok: bool
    message: str


# ── Chat ───────────────────────────────────────────────────────────────────────

class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class ChatResponse(BaseModel):
    session_id: str
    intent: str
    response: str
    provider_used: str
    history: list[HistoryItem]


class SpeechRequest(BaseModel):
    text: str = Field(..., min_length=1)


class TranscriptionResponse(BaseModel):
    ok: bool
    text: str


# ── Vision ─────────────────────────────────────────────────────────────────────

class VisionRequest(BaseModel):
    room: str | None = None  # None → default camera


class VisionResponse(BaseModel):
    ok: bool
    room: str | None
    description: str


# ── Devices ────────────────────────────────────────────────────────────────────

class LightActionRequest(BaseModel):
    room: str
    action: Literal["on", "off"]


class DeviceActionResponse(BaseModel):
    ok: bool
    message: str


# ── Rooms & Devices CRUD ───────────────────────────────────────────────────────

class CameraIn(BaseModel):
    name: str
    source_url: str
    username: str | None = None
    password: str | None = None
    is_default: bool = False


class CameraOut(CameraIn):
    id: uuid.UUID
    room_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class DeviceIn(BaseModel):
    name: str
    entity_id: str
    domain: str
    device_type: str
    config: dict[str, Any] | None = None


class DeviceOut(DeviceIn):
    id: uuid.UUID
    room_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class RoomIn(BaseModel):
    name: str
    friendly_name: str | None = None
    devices: list[DeviceIn] = []
    cameras: list[CameraIn] = []


class RoomOut(BaseModel):
    id: uuid.UUID
    name: str
    friendly_name: str | None
    devices: list[DeviceOut] = []
    cameras: list[CameraOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Memory / RAG ───────────────────────────────────────────────────────────────

class MemoryOut(BaseModel):
    id: uuid.UUID
    title: str | None
    content: str
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentIn(BaseModel):
    filename: str
    content: str


class DocumentOut(DocumentIn):
    id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ── System Config ──────────────────────────────────────────────────────────────

class ConfigEntry(BaseModel):
    key: str
    value: Any
    description: str | None = None


class ConfigUpdateRequest(BaseModel):
    value: Any
    description: str | None = None


# ── Health ─────────────────────────────────────────────────────────────────────

class ServiceStatus(BaseModel):
    name: str
    ok: bool
    message: str


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    services: list[ServiceStatus]
