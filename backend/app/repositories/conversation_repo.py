import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import Conversation


class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save(
        self,
        session_id: str,
        role: str,
        content: str,
        intent: str | None = None,
        provider: str | None = None,
    ) -> Conversation:
        row = Conversation(
            session_id=session_id,
            role=role,
            content=content,
            intent=intent,
            provider=provider,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def get_by_session(
        self, session_id: str, limit: int = 50
    ) -> list[Conversation]:
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.session_id == session_id)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
        )
        rows = list(result.scalars().all())
        return list(reversed(rows))

    async def get_all_sessions(self) -> list[str]:
        result = await self.db.execute(
            select(Conversation.session_id).distinct()
        )
        return [r for (r,) in result.all()]
