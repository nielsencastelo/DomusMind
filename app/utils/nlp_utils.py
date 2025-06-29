

from difflib import get_close_matches

# Lista de palavras-chave associadas a comandos de visão
vision_keywords = ["procure", "localize", "onde", "veja", "identifique", "encontre", "visualize", "detectar", "mostre", "observe", "camera", "video"]
WAKE_WORDS = ["coca", "hey coca", "ola coca", "fala coca" "koka", "ola koka", "Boca" "boca", "cuca"]
EXIT_WORDS = [
    "sair", "encerrar", "tchau", "desligar",
    "fechar", "parar", "até logo", "até mais",
    "finalizar", "desconectar", "encerrando"
]

def check_exit_command(text):
    text_lower = text.lower()
    return any(palavra in text_lower for palavra in EXIT_WORDS)


# Verifica se alguma palavra-chave está no texto
def check_vision_intent(text):
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in vision_keywords)


def check_wake_word(text):
    text_lower = text.lower()
    return any(wake_word in text_lower for wake_word in WAKE_WORDS)

# def check_wake_word(text):
#     text_lower = text.lower()
#     matches = get_close_matches(text_lower, WAKE_WORDS, n=1, cutoff=0.5)
#     return bool(matches)

