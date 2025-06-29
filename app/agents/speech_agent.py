# app/agents/search_agent.py
from utils.search_util import realizar_busca_web

class SearchAgent:
    def __init__(self, max_results=5, save_dir="search_logs"):
        self.max_results = max_results
        self.save_dir = save_dir

    def search_and_summarize(self, query_text: str) -> tuple[str, str]:
        """
        Executa a busca, salva o resultado e retorna um resumo e o caminho do arquivo salvo.
        """
        return realizar_busca_web(
            query_text=query_text,
            max_results=self.max_results,
            save_dir=self.save_dir
        )
