# app/agents/speech_agent.py
from utils.voz_utils import speak_text_with_mms

class SpeechAgent:
    def speak(self, text: str):
        speak_text_with_mms(text)
