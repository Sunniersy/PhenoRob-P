"""add index on task_events.task_id

Revision ID: 0007_add_task_events_index
Revises: 0006_add_indexes
Create Date: 2026-06-04 00:00:00
"""

from alembic import op


revision = "0007_add_task_events_index"
down_revision = "0006_add_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # TaskEvent - task_id used in timeline queries
    op.create_index("ix_task_events_task_id", "task_events", ["task_id"])


def downgrade() -> None:
    op.drop_index("ix_task_events_task_id", table_name="task_events")
