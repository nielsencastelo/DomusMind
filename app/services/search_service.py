from duckduckgo_search import DDGS


class SearchService:
    def __init__(self, max_results: int = 5):
        self.max_results = max_results

    def search(self, query: str) -> list[dict]:
        results: list[dict] = []

        try:
            with DDGS() as ddgs:
                raw_results = ddgs.text(query, max_results=self.max_results)
                for item in raw_results:
                    results.append(
                        {
                            "title": item.get("title", "").strip(),
                            "href": item.get("href", "").strip(),
                            "body": item.get("body", "").strip(),
                        }
                    )
        except Exception:
            return []

        return results

    def format_results(self, query: str, results: list[dict]) -> str:
        if not results:
            return f"Nenhum resultado relevante foi encontrado para: {query}"

        lines = [f"Consulta: {query}", "", "Resultados:"]
        for idx, item in enumerate(results, start=1):
            title = item.get("title", "")
            href = item.get("href", "")
            body = item.get("body", "")
            lines.append(f"{idx}. {title}")
            if body:
                lines.append(f"Resumo: {body}")
            if href:
                lines.append(f"Link: {href}")
            lines.append("")

        return "\n".join(lines).strip()

    def search_and_summarize(self, query: str) -> tuple[str, str]:
        results = self.search(query)
        formatted = self.format_results(query, results)
        return formatted, "duckduckgo"