# app/agents/vision_agent.py
from utils.vision_utils import capture_image_and_describe

class VisionAgent:
    def capture_and_describe(self) -> str:
        return capture_image_and_describe()
