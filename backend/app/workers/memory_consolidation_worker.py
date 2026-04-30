import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.celery import celery_app
from app.core.database import AsyncSessionLocal
from app.models.db_models import Conversation
from app.repositories.memory_repo import MemoryRepository
from app.services.llm_router import LLMRouter
from app.services.rag_service import RAGService


@celery_app.task(name="app.workers.memory_consolidation_worker.consolidate_recent_conversations")
def consolidate_recent_conversations() -> dict[str, int | str]:
    return asyncio.run(_consolidate_recent_conversations())


async def _consolidate_recent_conversations() -> dict[str, int | str]:
    since = datetime.now(timezone.utc) - timedelta(hours=1)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Conversation)
            .where(Conversation.created_at >= since)
            .order_by(Conversation.session_id, Conversation.created_at)
        )
        rows = list(result.scalars().all())

    if not rows:
        return {"status": "ok", "created": 0}

    grouped: dict[str, list[Conversation]] = {}
    for row in rows:
        grouped.setdefault(row.session_id, []).append(row)

    router = LLMRouter()
    rag = RAGService()
    created = 0

    async with AsyncSessionLocal() as db:
        repo = MemoryRepository(db)
        for session_id, turns in grouped.items():
            transcript = "\n".join(f"{t.role}: {t.content}" for t in turns)
            messages = router.build_messages(
                transcript,
                system_prompt=(
                    "Resuma esta conversa em uma memoria curta para RAG. "
                    "Preserve preferencias, fatos, decisoes e configuracoes uteis. "
                    "Ignore conversa fiada sem valor futuro."
                ),
            )
            try:
                summary, provider = await router.ainvoke(messages, temperature=0.1)
            except Exception:
                continue

            summary = summary.strip()
            if not summary:
                continue

            embedding = await rag.embed(summary)
            await repo.save_memory(
                title=f"Conversa {session_id}",
                content=summary,
                embedding=embedding,
                source="conversation",
                metadata={"session_id": session_id, "provider": provider},
            )
            created += 1

    return {"status": "ok", "created": created}
