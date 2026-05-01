"""Clear saved camera passwords.

Revision ID: 003_clear_default_camera_password
Revises: 002
Create Date: 2026-05-01
"""

from alembic import op


revision = "003_clear_default_camera_password"
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
