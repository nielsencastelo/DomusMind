# Lista de palavras-chave associadas a comandos de visão
vision_keywords = ["procure", "localize", "onde", "veja", "identifique", "encontre", "visualize", "detectar", "mostre", "observe"]

# Verifica se alguma palavra-chave está no texto
def check_vision_intent(text):
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in vision_keywords)
