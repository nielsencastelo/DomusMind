# app/agents/light_agent.py
from utils.llm_utils import ask_llm_ollama

class LightAgent:
    def __init__(self, model_name="phi4"):
        self.model_name = model_name

    def get_light_entity_id(self, user_input, history=[]):
        """
        Dado um comando de voz, retorna o entity_id da luz correspondente,
        com base nas configurações de rooms.json.
        """
        return ask_llm_ollama(user_input, history, self.model_name)
