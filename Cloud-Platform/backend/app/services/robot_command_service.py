from datetime import datetime, timezone

from sqlalchemy import desc, func, select

from backend.app.errors import UpstreamError
from backend.app.models import Robot, RobotCommand
from backend.app.pagination import build_paginated_payload
from shared.enums import RobotCommandStatus


class RobotCommandService:
    COMMAND_WHITELIST = {
        "start_task",
        "pause_task",
        "resume_task",
        "cancel_task",
        "return_home",
        "start_charge",
        "stop_charge",
        "capture_image",
    }

    def __init__(self, db, realtime, transport):
        self.db = db
        self.realtime = realtime
        self.transport = transport

    def issue_command(self, robot_id: str, payload: dict, operator: str | None = None) -> dict:
        with self.db.session_scope() as session:
            robot = session.get(Robot, robot_id)
            if not robot:
                raise ValueError("robot not found")
            command = payload.get("command")
            if command not in self.COMMAND_WHITELIST:
                raise ValueError("unsupported robot command")
            params = payload.get("params", {})
            if not isinstance(params, dict):
                raise ValueError("params must be an object")

            record = RobotCommand(
                robot_id=robot.id,
                command=command,
                status=RobotCommandStatus.PENDING.value,
                operator=operator or payload.get("operator"),
                params_json=params,
            )
            session.add(record)
            session.flush()

            record_id = record.id
            robot_code = robot.robot_code
            message = {
                "command_id": record_id,
                "robot_id": robot_code,
                "command": command,
                "params": params,
                "operator": record.operator,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "protocol_version": "1.0",
            }
            session.commit()
            try:
                self.transport.publish_command(robot_code, message)
            except Exception as exc:
                self._mark_command_failed(session, record_id, robot_code, message, exc)
                raise UpstreamError("robot command dispatch failed", errors={"detail": str(exc)}) from exc

            record = session.get(RobotCommand, record_id)
            record.status = RobotCommandStatus.SENT.value
            session.commit()
            data = self.serialize_command(record, robot)
            self.realtime.publish("robot.command_updated", data)
            return data

    def list_commands(self, robot_id: str, filters: dict | None = None) -> dict:
        filters = filters or {"page": 1, "page_size": 20}
        with self.db.session_scope() as session:
            robot = session.get(Robot, robot_id)
            if not robot:
                raise ValueError("robot not found")
            query = select(RobotCommand).where(RobotCommand.robot_id == robot.id)
            if filters.get("status"):
                query = query.where(RobotCommand.status == filters["status"])
            total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
            commands = session.scalars(
                query.order_by(desc(RobotCommand.created_at))
                .offset((filters["page"] - 1) * filters["page_size"])
                .limit(filters["page_size"])
            ).all()
            return build_paginated_payload(
                [self.serialize_command(item, robot) for item in commands], total, filters["page"], filters["page_size"]
            )

    def _mark_command_failed(self, session, record_id: str, robot_code: str, message: dict, exc: Exception) -> None:
        session.rollback()
        record = session.get(RobotCommand, record_id)
        if record:
            record.status = RobotCommandStatus.FAILED.value
            record.error_message = str(exc)
            record.completed_at = datetime.now(timezone.utc)
            session.commit()
        self.realtime.publish(
            "system.alert",
            {
                "source": "robot_command",
                "message": "机器人命令下发失败",
                "robot_code": robot_code,
                "error": str(exc),
                "payload": message,
            },
        )

    @staticmethod
    def serialize_command(command: RobotCommand | None, robot: Robot | None = None) -> dict | None:
        if not command:
            return None
        return {
            "id": command.id,
            "robot_id": command.robot_id,
            "robot_code": robot.robot_code if robot else None,
            "command": command.command,
            "status": command.status,
            "operator": command.operator,
            "params": command.params_json,
            "result": command.result_json,
            "error_message": command.error_message,
            "accepted_at": command.accepted_at.isoformat(),
            "completed_at": command.completed_at.isoformat() if command.completed_at else None,
            "created_at": command.created_at.isoformat(),
            "updated_at": command.updated_at.isoformat(),
        }
