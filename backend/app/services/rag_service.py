from app.core.settings import settings


class RAGService:
    """
    Embedding and RAG helpers.
    Uses Google text-embedding-004 as primary, nomic-embed-text (Ollama) as fallback.
    """

    def __init__(self):
        self._google_embedders = {}
        self._ollama_embedders = {}

    @staticmethod
    async def _embedding_config() -> dict:
        try:
            from app.core.database import AsyncSessionLocal
            from app.repositories.config_repo import ConfigRepository

            async with AsyncSessionLocal() as db:
                repo = ConfigRepository(db)
                value = await repo.get("embedding.config")
                llm_providers = await repo.get("llm.providers")
                gemini_config = (
                    llm_providers.get("gemini", {})
                    if isinstance(llm_providers, dict)
                    else {}
                )
                if isinstance(value, dict):
                    return {
                        **value,
                        "google_api_key": gemini_config.get("api_key") or settings.gemini_api_key,
                    }
                provider = await repo.get("embedding.provider")
                model = await repo.get("embedding.model")
                return {
                    "provider": provider or settings.embedding_provider,
                    "model": model or "nomic-embed-text",
                    "google_api_key": gemini_config.get("api_key") or settings.gemini_api_key,
                }
        except Exception:
            return {
                "provider": settings.embedding_provider,
                "model": "nomic-embed-text",
            }

    def _get_google_embedder(self, api_key: str):
        if api_key not in self._google_embedders:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            self._google_embedders[api_key] = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=api_key,
            )
        return self._google_embedders[api_key]

    def _get_ollama_embedder(self, model: str):
        if model not in self._ollama_embedders:
            from langchain_ollama import OllamaEmbeddings
            self._ollama_embedders[model] = OllamaEmbeddings(
                model=model,
                base_url=settings.ollama_base_url,
            )
        return self._ollama_embedders[model]

    async def embed(self, text: str) -> list[float] | None:
        """Generate embedding vector for a text string."""
        cfg = await self._embedding_config()
        provider = str(cfg.get("provider") or settings.embedding_provider)
        model_name = str(cfg.get("model") or "nomic-embed-text")
        google_api_key = str(cfg.get("google_api_key") or settings.gemini_api_key)
        try:
            if provider == "google" and google_api_key:
                embedder = self._get_google_embedder(google_api_key)
                return await embedder.aembed_query(text)
        except Exception:
            pass

        try:
            embedder = self._get_ollama_embedder(model_name)
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
