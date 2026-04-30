import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import Document, Memory


class MemoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Memories ──────────────────────────────────────────────────────────

    async def save_memory(
        self,
        content: str,
        embedding: list[float] | None,
        title: str | None = None,
        source: str = "conversation",
        metadata: dict | None = None,
    ) -> Memory:
        mem = Memory(
            title=title,
            content=content,
            embedding=embedding,
            source=source,
            metadata_=metadata,
        )
        self.db.add(mem)
        await self.db.commit()
        await self.db.refresh(mem)
        return mem

    async def similarity_search(
        self,
        embedding: list[float],
        limit: int = 5,
        threshold: float = 0.7,
    ) -> list[Memory]:
        """Cosine similarity search via pgvector."""
        result = await self.db.execute(
            select(Memory)
            .where(Memory.embedding.isnot(None))
            .order_by(Memory.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_all(self, limit: int = 100) -> list[Memory]:
        result = await self.db.execute(
            select(Memory).order_by(Memory.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def delete(self, memory_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(Memory).where(Memory.id == memory_id)
        )
        mem = result.scalar_one_or_none()
        if not mem:
            return False
        await self.db.delete(mem)
        await self.db.commit()
        return True

    # ── Documents ─────────────────────────────────────────────────────────

    async def save_document(
        self,
        filename: str,
        content: str,
        embedding: list[float] | None,
        metadata: dict | None = None,
    ) -> Document:
        doc = Document(
            filename=filename,
            content=content,
            embedding=embedding,
            metadata_=metadata,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def document_similarity_search(
        self,
        embedding: list[float],
        limit: int = 5,
    ) -> list[Document]:
        result = await self.db.execute(
            select(Document)
            .where(Document.embedding.isnot(None))
            .order_by(Document.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_all_documents(self) -> list[Document]:
        result = await self.db.execute(
            select(Document).order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def combined_search(
        self, embedding: list[float], limit: int = 5
    ) -> list[str]:
        """Search memories + documents, return list of content strings."""
        memories = await self.similarity_search(embedding, limit=limit)
        docs = await self.document_similarity_search(embedding, limit=limit)
        results = [m.content for m in memories] + [d.content for d in docs]
        return results[:limit]
