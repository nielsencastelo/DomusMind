from app.core.settings import settings


class RAGService:
    """
    Embedding and RAG helpers.
    Uses Google text-embedding-004 as primary, nomic-embed-text (Ollama) as fallback.
    """

    def __init__(self):
        self._google_embedder = None
        self._ollama_embedder = None

    def _get_google_embedder(self):
        if self._google_embedder is None:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            self._google_embedder = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=settings.gemini_api_key,
            )
        return self._google_embedder

    def _get_ollama_embedder(self):
        if self._ollama_embedder is None:
            from langchain_ollama import OllamaEmbeddings
            self._ollama_embedder = OllamaEmbeddings(
                model="nomic-embed-text",
                base_url=settings.ollama_base_url,
            )
        return self._ollama_embedder

    async def embed(self, text: str) -> list[float] | None:
        """Generate embedding vector for a text string."""
        try:
            if settings.embedding_provider == "google" and settings.gemini_api_key:
                embedder = self._get_google_embedder()
                return await embedder.aembed_query(text)
        except Exception:
            pass

        try:
            embedder = self._get_ollama_embedder()
            return await embedder.aembed_query(text)
        except Exception:
            return None

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts (for batch indexing)."""
        results = []
        for text in texts:
            vec = await self.embed(text)
            if vec:
                results.append(vec)
        return results

    def format_context(self, chunks: list[str]) -> str:
        if not chunks:
            return ""
        formatted = "\n\n".join(
            f"[Memória {i + 1}]: {chunk}" for i, chunk in enumerate(chunks)
        )
        return f"Contexto de memórias relevantes:\n{formatted}"
