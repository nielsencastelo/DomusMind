from langchain_core.messages import AIMessage, HumanMessage
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import json

# ------------------------------ Configuração do Modelo ------------------------------
def model_ollama(model, temperature=0.1):
    """Retorna uma instância do modelo LLM especificado."""
    return ChatOllama(model=model.lower().replace(" ", ""), temperature=temperature)


def interpretar_comando(user_query, chat_history, model_name, comodo, objetos):
    """Gera uma resposta baseada na interação do usuário com o modelo de IA."""
    try:
        llm = model_ollama(model_name)

        system_prompt = f"""
            Você é um assistente inteligente para automação residencial.
            No cômodo '{comodo}', a câmera viu: {objetos}.
            Utilize raciocínio estruturado seguindo o método cadeia de pensamento (chain-of-thought):

            1. Compreenda claramente o comando do usuário.
            2. Identifique qual ação deve ser executada (ligar dispositivo, informar status, alterar configuração).
            3. Se o usuário quiser conversar seja simples e direto nas respostas.
            4. Execute (simule) a ação solicitada.
            5. Confirme a execução ou forneça a informação solicitada ao usuário de forma clara e amigável.

            Sempre responda com linguagem simples e amigável, adequada para uma conversa casual dentro de casa.
            Não mencione sua análise ou interpretação ao usuário, apenas confirme diretamente a execução da ação.
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

def interpretar_comando_old(comodo, texto, objetos, model_name="gemma3:27b"):
    """Interpreta comandos usando o modelo Ollama configurado anteriormente."""
    try:
        llm = model_ollama(model_name)

        prompt = f"""
        Você é um assistente inteligente para automação residencial.
        No cômodo '{comodo}', foi dito: "{texto}". A câmera viu: {objetos}.

        Identifique claramente a ação necessária e retorne apenas um JSON com campos 'acao' e 'complemento', por exemplo:
        {{"acao": "ligar_luz", "complemento": "forte"}}
        """

        response = llm.invoke(prompt)
        acao_json = json.loads(response.content)
        return acao_json

    except Exception:
        return {"acao": "erro", "complemento": "não consegui interpretar"}

# Exemplo de uso
# resultado = interpretar_comando("sala", "Ligue as luzes, por favor.", ["sofá", "mesa"])
# print(resultado)
