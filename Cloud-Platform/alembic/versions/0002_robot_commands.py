"""robot commands and platform hardening

Revision ID: 0002_robot_commands
Revises: 0001_initial_schema
Create Date: 2026-04-18 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_robot_commands"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "robot_commands",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("robot_id", sa.String(length=36), sa.ForeignKey("robots.id"), nullable=False),
        sa.Column("command", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("operator", sa.String(length=128), nullable=True),
        sa.Column("params_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("result_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("robot_commands")
