"""Add extended fields to cameras table

Revision ID: 002
Revises: 001
Create Date: 2026-05-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cameras", sa.Column("camera_type", sa.String(20), nullable=False, server_default="ip"))
    op.add_column("cameras", sa.Column("channel", sa.Integer, nullable=True))
    op.add_column("cameras", sa.Column("is_local", sa.Boolean, nullable=False, server_default="false"))
    op.add_column("cameras", sa.Column("device_path", sa.String(200), nullable=True))
    op.add_column("cameras", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("cameras", sa.Column("resolution", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("cameras", "resolution")
    op.drop_column("cameras", "last_seen_at")
    op.drop_column("cameras", "device_path")
    op.drop_column("cameras", "is_local")
    op.drop_column("cameras", "channel")
    op.drop_column("cameras", "camera_type")
