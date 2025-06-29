# app/agents/intent_classifier_agent.py
from utils.llm_utils import model_ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class IntentClassifierAgent:
    def __init__(self, model_name="phi4"):
        self.model_name = model_name
        self.llm = model_ollama(self.model_name, temperature=0.0)  # baixa temperatura para respostas determinísticas

        self.prompt_template = ChatPromptTemplate.from_template("""
Você é um classificador de intenções de comandos de voz para uma casa inteligente. 
Dado um texto de transcrição, classifique a intenção principal entre as seguintes opções:

- "visao" → se for algo relacionado a ver, detectar, observar câmeras ou pessoas
- "pesquisa" → se for algo relacionado a buscar ou pesquisar na internet
- "sair" → se for algo como "encerrar", "tchau", "desligar", "até mais"
- "outro" → se não corresponder a nenhuma das intenções acima

Transcrição: "{input}"

Responda apenas com uma das palavras: visao, pesquisa, sair, outro.
        """)

        self.chain = self.prompt_template | self.llm | StrOutputParser()

    def classify(self, transcribed_text: str) -> str:
        try:
            return self.chain.invoke({"input": transcribed_text}).strip().lower()
        except Exception:
            return "outro"
