
# search_keywords = [
#     "pesquise", "procure na internet", "busque", "veja na internet",
#     "ache online", "me diga o que é", "pesquisa web", "descubra sobre", "o que é"
# ]

# vision_keywords = [
#     "procure", "localize", "onde", "veja", "identifique", "encontre",
#     "visualize", "detectar", "mostre", "observe", "camera", "vídeo", "quantas pessoas", "quem está", "o que tem"
# ]

# WAKE_WORDS = ["coca", "hey coca", "ola coca", "fala coca" "koka", "ola koka", "Boca" "boca", "cuca"]

# EXIT_WORDS = [
#     "sair", "encerrar", "tchau", "desligar",
#     "fechar", "parar", "até logo", "até mais",
#     "finalizar", "desconectar", "encerrando"
# ]

# def check_exit_command(text):
#     text_lower = text.lower()
#     return any(palavra in text_lower for palavra in EXIT_WORDS)


# import re



# def normalize_text(text):
#     text = text.lower()
#     text = re.sub(r"[^\w\s]", "", text)  # remove pontuação
#     return text.strip()

# def check_vision_intent(text: str) -> bool:
#     text = normalize_text(text)
#     for keyword in vision_keywords:
#         if keyword in text:
#             return True
#     return False


# def check_search_intent(text: str) -> bool:
#     text_lower = text.lower()
#     return any(keyword in text_lower for keyword in search_keywords)

# def check_wake_word(text):
#     text_lower = text.lower()
#     return any(wake_word in text_lower for wake_word in WAKE_WORDS)

