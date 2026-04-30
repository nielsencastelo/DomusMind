from duckduckgo_search import DDGS


class SearchService:
    def __init__(self, max_results: int = 5):
        self.max_results = max_results

    def search(self, query: str) -> list[dict]:
        try:
            with DDGS() as ddgs:
                return [
                    {
                        "title": r.get("title", "").strip(),
                        "href": r.get("href", "").strip(),
                        "body": r.get("body", "").strip(),
                    }
                    for r in ddgs.text(query, max_results=self.max_results)
                ]
        except Exception:
            return []

    def format_results(self, query: str, results: list[dict]) -> str:
        if not results:
            return f"Nenhum resultado encontrado para: {query}"
        lines = [f"Consulta: {query}", "", "Resultados:"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r['title']}")
            if r["body"]:
                lines.append(f"   {r['body']}")
            if r["href"]:
                lines.append(f"   {r['href']}")
            lines.append("")
        return "\n".join(lines).strip()

    def search_and_format(self, query: str) -> str:
        results = self.search(query)
        return self.format_results(query, results)
