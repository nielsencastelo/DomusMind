"""Clear saved camera passwords.

Revision ID: 003
Revises: 002
Create Date: 2026-05-01
"""

from alembic import op


revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE cameras
        SET
            password = NULL,
            source_url = regexp_replace(source_url, '://([^:/@]+):[^@]+@', '://\\1@')
        WHERE
            password IS NOT NULL
            OR source_url ~ '://[^:/@]+:[^@]+@';
        """
    )


def downgrade() -> None:
    pass
