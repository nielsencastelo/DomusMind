from utils.llm_utils import model_ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils.nlp_utils import WAKE_WORDS

wake_words_str = ", ".join(f'"{w}"' for w in WAKE_WORDS)

class IntentClassifierAgent:
    def __init__(self, model_name="phi4"):
        self.model_name = model_name
        self.llm = model_ollama(self.model_name, temperature=0.0)

        self.prompt_template = ChatPromptTemplate.from_template(f"""
        Você é um classificador de intenções para comandos de voz em uma casa inteligente.
        Todos os comandos válidos contêm um nome de ativação (wake word) como um dos seguintes:
        {wake_words_str}

        Sua tarefa é classificar a **intenção principal** da frase. Responda apenas com uma destas opções:
        - "visao" → se o comando for sobre ver, detectar, checar câmeras, contar pessoas, observar ambiente.
        - "pesquisa" → se for sobre pesquisar algo na internet, entender um conceito, buscar informações.
        - "luz" → se for claramente um comando para ligar, acender, apagar ou desligar uma luz, lâmpada ou iluminação.
        - "sair" → apenas se for claramente para encerrar o programa, desligar o assistente ou parar o sistema.
        - "outro" → qualquer outro comando que não se encaixe nos anteriores.

        ❗️Importante: só classifique como "sair" se o comando for claro e direto como:
        - "coca, finalize o programa"
        - "koka, encerre o assistente"
        - "coca, desligue o sistema"
        - "pare tudo agora"
        - "encerre imediatamente"

        ❌ NÃO considere frases como "valeu", "tchau", "até mais" como sair. Classifique isso como "outro".

        Exemplos:
        1. "kouka, veja quem está na porta" → visao
        2. "koka, o que é aprendizado de máquina?" → pesquisa
        3. "cuca, finalize o programa agora" → sair
        4. "coca, desligue todas as luzes da casa" → luz
        5. "koka, acenda a luz do escritório" → luz
        6. "coca, tchau por hoje" → outro

        Transcrição: "{{input}}"

        Responda apenas com: visao, pesquisa, luz, sair ou outro.
        """)

        self.chain = self.prompt_template | self.llm | StrOutputParser()

    def classify(self, transcribed_text: str) -> str:
        try:
            return self.chain.invoke({"input": transcribed_text}).strip().lower()
        except Exception:
            return "outro"
