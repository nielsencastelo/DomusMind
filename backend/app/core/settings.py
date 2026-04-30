from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "DomusMind"
    env: str = "dev"
    debug: bool = False

    # ── Database ──────────────────────────────────────────────────────────
    database_url: str = (
        "postgresql+asyncpg://domusmind:domusmind@localhost:5432/domusmind"
    )

    # ── Redis ─────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    redis_session_ttl: int = 3600  # seconds

    # ── LLM ───────────────────────────────────────────────────────────────
    local_model: str = "phi4"
    ollama_base_url: str = "http://localhost:11434"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"
    # Gemini first — best cost/performance; local as offline fallback
    llm_fallback_chain: str = "gemini,local,openai,claude"

    # ── Home Assistant ────────────────────────────────────────────────────
    hass_url: str = "http://localhost:8123"
    hass_token: str = ""

    # ── Camera ────────────────────────────────────────────────────────────
    camera_ip: str = "192.168.2.218"
    camera_user: str = "admin"
    camera_password: str = ""
    # RTSP URL built from the camera fields when not overridden
    default_camera_source: str = "0"
    yolo_weights: str = "models/yolov8x.pt"

    # ── Audio ─────────────────────────────────────────────────────────────
    audio_sample_rate: int = 16000
    whisper_model: str = "medium"
    whisper_compute_type: str = "float32"

    # ── TTS ───────────────────────────────────────────────────────────────
    tts_model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    tts_speaker_wav: str = "models/Voz_Nielsen.wav"
    tts_language: str = "pt"
    tts_fallback_sr: int = 24000

    # ── Embeddings ────────────────────────────────────────────────────────
    embedding_dim: int = 768
    # "google" uses text-embedding-004; "local" uses nomic-embed-text via Ollama
    embedding_provider: str = "google"

    @property
    def rtsp_url(self) -> str:
        return (
            f"rtsp://{self.camera_user}:{self.camera_password}"
            f"@{self.camera_ip}:554/stream"
        )


settings = Settings()
