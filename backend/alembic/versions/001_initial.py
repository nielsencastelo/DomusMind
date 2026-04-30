"""Initial schema with pgvector

Revision ID: 001
Revises:
Create Date: 2026-04-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 768


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── rooms ────────────────────────────────────────────────────────────
    op.create_table(
        "rooms",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("friendly_name", sa.String(200)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
    )

    # ── devices ──────────────────────────────────────────────────────────
    op.create_table(
        "devices",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "room_id",
            UUID(as_uuid=True),
            sa.ForeignKey("rooms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(200), nullable=False),
        sa.Column("domain", sa.String(50), nullable=False),
        sa.Column("device_type", sa.String(50), nullable=False),
        sa.Column("config", JSONB),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
    )

    # ── cameras ──────────────────────────────────────────────────────────
    op.create_table(
        "cameras",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "room_id",
            UUID(as_uuid=True),
            sa.ForeignKey("rooms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("source_url", sa.String(500), nullable=False),
        sa.Column("username", sa.String(100)),
        sa.Column("password", sa.String(200)),
        sa.Column("is_default", sa.Boolean, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
    )

    # ── conversations ────────────────────────────────────────────────────
    op.create_table(
        "conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", sa.String(100), nullable=False, index=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("intent", sa.String(50)),
        sa.Column("provider", sa.String(50)),
        sa.Column("metadata", JSONB),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_conversations_session_id", "conversations", ["session_id"])

    # ── memories ─────────────────────────────────────────────────────────
    op.create_table(
        "memories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(500)),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("source", sa.String(200), server_default="conversation"),
        sa.Column("embedding", Vector(EMBEDDING_DIM)),
        sa.Column("metadata", JSONB),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
    )
    op.execute(
        f"CREATE INDEX ix_memories_embedding ON memories "
        f"USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    # ── documents ────────────────────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM)),
        sa.Column("metadata", JSONB),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
    )
    op.execute(
        f"CREATE INDEX ix_documents_embedding ON documents "
        f"USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    # ── system_config ────────────────────────────────────────────────────
    op.create_table(
        "system_config",
        sa.Column("key", sa.String(200), primary_key=True),
        sa.Column("value", JSONB, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("system_config")
    op.drop_table("documents")
    op.drop_table("memories")
    op.drop_table("conversations")
    op.drop_table("cameras")
    op.drop_table("devices")
    op.drop_table("rooms")
    op.execute("DROP EXTENSION IF EXISTS vector")
