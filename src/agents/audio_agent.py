# app/agents/audio_agent.py
from utils.audio_utils import capture_audio_and_transcribe_continuous

class AudioAgent:
    def listen_and_transcribe(self) -> str:
        return capture_audio_and_transcribe_continuous()
