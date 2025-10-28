# app/agents/llm_agent.py
from utils.llm_utils import ask_llm_ollama

class LLMAgent:
    def __init__(self, model_name="phi4"):
        self.model_name = model_name

    def ask(self, user_input, history=[]):
        return ask_llm_ollama(user_input, history, self.model_name)
