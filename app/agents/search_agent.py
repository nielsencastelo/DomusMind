from duckduckgo_search import DDGS

class SearchAgent:
    def __init__(self):
        self.engine = DDGS()

    def search(self, query: str, max_results: int = 5) -> list:
        """
        Faz uma busca na web usando DuckDuckGo e retorna os principais resultados.
        """
        results = []
        try:
            for r in self.engine.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title"),
                    "href": r.get("href"),
                    "body": r.get("body")
                })
        except Exception as e:
            results.append({"error": str(e)})

        return results
