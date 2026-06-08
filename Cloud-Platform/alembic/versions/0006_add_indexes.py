"""add indexes for frequently queried columns

Revision ID: 0006_add_indexes
Revises: 0005_add_refresh_tokens
Create Date: 2026-06-04 00:00:00
"""

from alembic import op


revision = "0006_add_indexes"
down_revision = "0005_add_refresh_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Task
    op.create_index("ix_tasks_status", "tasks", ["status"])
    op.create_index("ix_tasks_robot_id", "tasks", ["robot_id"])
    op.create_index("ix_tasks_created_at", "tasks", ["created_at"])

    # RobotCommand
    op.create_index("ix_robot_commands_robot_id", "robot_commands", ["robot_id"])
    op.create_index("ix_robot_commands_created_at", "robot_commands", ["created_at"])

    # RobotHeartbeat
    op.create_index("ix_robot_heartbeats_robot_id", "robot_heartbeats", ["robot_id"])

    # UploadSession
    op.create_index("ix_upload_sessions_task_id", "upload_sessions", ["task_id"])
    op.create_index("ix_upload_sessions_robot_id", "upload_sessions", ["robot_id"])

    # DataAsset
    op.create_index("ix_data_assets_task_id", "data_assets", ["task_id"])
    op.create_index("ix_data_assets_robot_id", "data_assets", ["robot_id"])

    # AnalysisJob
    op.create_index("ix_analysis_jobs_task_id", "analysis_jobs", ["task_id"])

    # AnalysisResult (task_id already has a unique constraint/index from unique=True)
    op.create_index("ix_analysis_results_task_id", "analysis_results", ["task_id"])

    # SystemAlert
    op.create_index("ix_system_alerts_created_at", "system_alerts", ["created_at"])
    op.create_index("ix_system_alerts_is_acknowledged", "system_alerts", ["is_acknowledged"])


def downgrade() -> None:
    op.drop_index("ix_system_alerts_is_acknowledged", table_name="system_alerts")
    op.drop_index("ix_system_alerts_created_at", table_name="system_alerts")
    op.drop_index("ix_analysis_results_task_id", table_name="analysis_results")
    op.drop_index("ix_analysis_jobs_task_id", table_name="analysis_jobs")
    op.drop_index("ix_data_assets_robot_id", table_name="data_assets")
    op.drop_index("ix_data_assets_task_id", table_name="data_assets")
    op.drop_index("ix_upload_sessions_robot_id", table_name="upload_sessions")
    op.drop_index("ix_upload_sessions_task_id", table_name="upload_sessions")
    op.drop_index("ix_robot_heartbeats_robot_id", table_name="robot_heartbeats")
    op.drop_index("ix_robot_commands_created_at", table_name="robot_commands")
    op.drop_index("ix_robot_commands_robot_id", table_name="robot_commands")
    op.drop_index("ix_tasks_created_at", table_name="tasks")
    op.drop_index("ix_tasks_robot_id", table_name="tasks")
    op.drop_index("ix_tasks_status", table_name="tasks")
