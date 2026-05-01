"""Clear hardcoded default camera password.

Revision ID: 003_clear_default_camera_password
Revises: 002_camera_fields
Create Date: 2026-05-01
"""

from alembic import op


revision = "003_clear_default_camera_password"
down_revision = "002_camera_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE cameras
        SET
            password = NULL,
            source_url = replace(source_url, ':globalsys123@', '@')
        WHERE
            password = 'globalsys123'
            OR source_url LIKE '%:globalsys123@%';
        """
    )


def downgrade() -> None:
    pass
