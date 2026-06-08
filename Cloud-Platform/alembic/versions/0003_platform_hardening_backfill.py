"""backfill platform hardening columns after legacy robot command migration

Revision ID: 0003_platform_hardening_backfill
Revises: 0002_platform_hardening
Create Date: 2026-04-20 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_platform_hardening_backfill"
down_revision = "0002_platform_hardening"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not _has_column("users", "must_change_password"):
        op.add_column("users", sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default=sa.true()))

    if not _has_column("tasks", "failure_reason"):
        op.add_column("tasks", sa.Column("failure_reason", sa.Text(), nullable=True))

    if not _has_column("tasks", "last_commanded_by"):
        op.add_column("tasks", sa.Column("last_commanded_by", sa.String(length=128), nullable=True))

    if not _has_column("system_alerts", "is_acknowledged"):
        op.add_column(
            "system_alerts",
            sa.Column("is_acknowledged", sa.Boolean(), nullable=False, server_default=sa.false()),
        )

    if not _has_column("system_alerts", "acknowledged_by"):
        op.add_column("system_alerts", sa.Column("acknowledged_by", sa.String(length=128), nullable=True))

    if not _has_column("system_alerts", "acknowledged_at"):
        op.add_column("system_alerts", sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    if _has_column("system_alerts", "acknowledged_at"):
        op.drop_column("system_alerts", "acknowledged_at")

    if _has_column("system_alerts", "acknowledged_by"):
        op.drop_column("system_alerts", "acknowledged_by")

    if _has_column("system_alerts", "is_acknowledged"):
        op.drop_column("system_alerts", "is_acknowledged")

    if _has_column("tasks", "last_commanded_by"):
        op.drop_column("tasks", "last_commanded_by")

    if _has_column("tasks", "failure_reason"):
        op.drop_column("tasks", "failure_reason")

    if _has_column("users", "must_change_password"):
        op.drop_column("users", "must_change_password")
