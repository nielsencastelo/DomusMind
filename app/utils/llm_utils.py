from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import AIMessage, HumanMessage

# ------------------------------ Configuração do Modelo ------------------------------
def model_ollama(model, temperature=0.1):
    """Retorna uma instância do modelo LLM especificado."""
    return ChatOllama(model=model.lower().replace(" ", ""), temperature=temperature)


def ask_llm_ollama(user_query, chat_history, model_name="phi4"):
    """Gera uma resposta baseada na interação do usuário com o modelo de IA."""
    try:
        llm = model_ollama(model_name)

        system_prompt = """
            Você é um assistente doméstico com percepção visual e auditiva.

            - Use a descrição da câmera, que lista os objetos detectados no ambiente.
            - Essa descrição já está filtrada e contém apenas objetos confiáveis, sem repetições ou incertezas.
            - Sua tarefa é interpretar a cena com base nesses objetos e responder à fala do usuário de forma clara, direta e natural.
            - Seja claro, educado e direto.
            - Respotas curtas.

            Comunique-se em português, como se estivesse no mesmo ambiente que o usuário.
            Evite termos técnicos e responda de forma acolhedora, útil e proativa.
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
        })

    except Exception:
        return "❌ Desculpe, não consegui entender ou realizar essa ação. Por favor, tente novamente."
