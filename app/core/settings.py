import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    app_name: str = os.getenv("APP_NAME", "DomusMind")
    env: str = os.getenv("ENV", "dev")

    local_model: str = os.getenv("LOCAL_MODEL", "phi4")
    openai_model: str = os.getenv("OPENAI_MODEL", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "")
    claude_model: str = os.getenv("CLAUDE_MODEL", "")
    llm_fallback_chain: str = os.getenv(
        "LLM_FALLBACK_CHAIN",
        "local,openai,gemini,claude",
    )

    hass_url: str = os.getenv("HASS_URL", "http://localhost:8123")
    hass_token: str | None = os.getenv("TOKEN")

    default_camera_source: str = os.getenv("DEFAULT_CAMERA_SOURCE", "0")
    yolo_weights: str = os.getenv("YOLO_WEIGHTS", "models/yolov8x.pt")

    audio_sample_rate: int = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
    whisper_model: str = os.getenv("WHISPER_MODEL", "medium")
    whisper_compute_type: str = os.getenv("WHISPER_COMPUTE_TYPE", "float32")

    tts_model_name: str = os.getenv(
        "TTS_MODEL_NAME",
        "tts_models/multilingual/multi-dataset/xtts_v2",
    )
    tts_speaker_wav: str = os.getenv("TTS_SPEAKER_WAV", "models/Voz_Nielsen.wav")
    tts_language: str = os.getenv("TTS_LANGUAGE", "pt")
    tts_fallback_sr: int = int(os.getenv("TTS_FALLBACK_SR", "24000"))

    rooms_config_path: str = os.getenv("ROOMS_CONFIG_PATH", "app/configs/rooms.json")


settings = Settings()