import os
import json
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage

def model_ollama(model, temperature=0.0):
    """Retorna uma instância do modelo LLM especificado."""
    return ChatOllama(model=model.lower().replace(" ", ""), temperature=temperature)

def get_room_light_mapping():
    """Lê o arquivo rooms.json e retorna descrição formatada das luzes por cômodo."""
    try:
        rooms_path = os.path.join(os.path.dirname(__file__), "..", "configs", "rooms.json")
        rooms_path = os.path.abspath(rooms_path)
        with open(rooms_path, "r", encoding="utf-8") as f:
            rooms = json.load(f)

        room_lines = []
        for room, info in rooms.items():
            entity = info.get("light_entity_id", "não definida")
            room_lines.append(f"- {room.capitalize()}: luz = {entity}")
        return "\n".join(room_lines)
    except Exception as e:
        return "⚠️ Erro ao carregar os cômodos. Nenhuma luz foi encontrada."

def ask_llm_ollama(user_query, chat_history, model_name="phi4"):
    """Gera uma resposta baseada na interação do usuário com o modelo de IA."""
    try:
        llm = model_ollama(model_name)

        room_description = get_room_light_mapping()

        system_prompt = f"""
        Você é um assistente doméstico inteligente com acesso a luzes conectadas via Home Assistant.

        Abaixo estão os cômodos e suas luzes disponíveis:
        {room_description}

        Sua função é:
        - Interpretar qual luz o usuário deseja acender ou apagar com base em sua fala.
        - Informar exatamente o nome da entidade da luz correspondente ao cômodo desejado.
        - Se não entender o cômodo, diga que não foi possível identificar.

        Exemplo de resposta esperada:
        "switch.sonoff_10013abe9c_1"

        Não use frases completas, apenas o `entity_id` correspondente.

        Comunique-se de forma objetiva.
        """

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}")
        ])

        chain = prompt_template | llm | StrOutputParser()

        return chain.invoke({
            "chat_history": chat_history,
            "input": user_query
        }).strip()

    except Exception:
        return "❌"
