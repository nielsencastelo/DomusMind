# comunicação com ollama
from openai import OpenAI

client = OpenAI(api_key="SUA_API")

def interpretar_comando(comodo, texto, objetos):
    prompt = f"""
Você é um assistente de uma casa inteligente. No cômodo '{comodo}', foi dito: "{texto}". A câmera viu: {objetos}.
Gere ações no formato JSON com campo 'acao' e 'complemento', por exemplo: {{"acao": "ligar_luz", "complemento": "forte"}}.
"""
    resposta = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return resposta.choices[0].message.content
