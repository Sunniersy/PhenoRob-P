"""disable demo analysis provider default

Revision ID: 0004_demo_default_off
Revises: 0003_platform_hardening_backfill
Create Date: 2026-04-20 12:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_demo_default_off"
down_revision = "0003_platform_hardening_backfill"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "analysis_jobs",
        "provider",
        existing_type=sa.String(length=64),
        server_default="disabled",
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "analysis_jobs",
        "provider",
        existing_type=sa.String(length=64),
        server_default="demo",
        existing_nullable=False,
    )
