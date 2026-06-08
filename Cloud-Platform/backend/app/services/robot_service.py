from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, func, select

from backend.app.models import Robot, RobotCommand, RobotHeartbeat, Task, TaskEvent
from backend.app.pagination import build_paginated_payload
from backend.app.services.robot_command_service import RobotCommandService
from backend.app.validators import escape_like_wildcards
from shared.enums import RobotCommandStatus, RobotStatus, TaskEventType, TaskStatus
from shared.state_machine import TaskStateMachine


class RobotService:
    def __init__(self, db, realtime, transport):
        self.db = db
        self.realtime = realtime
        self.transport = transport
        self.command_service = RobotCommandService(db, realtime, transport)

    def register_robot(self, payload: dict) -> dict:
        with self.db.session_scope() as session:
            self._validate_robot_registration(session, payload)
            robot = Robot(
                robot_code=payload["robot_code"],
                name=payload["name"],
                status=payload.get("status", RobotStatus.IDLE.value),
                protocol=payload.get("protocol", "mqtt"),
                capabilities=payload.get("capabilities", {}),
                metadata_json=payload.get("metadata", {}),
            )
            session.add(robot)
            session.commit()
            return self.serialize_robot(robot)

    def list_robots(self, filters: dict | None = None) -> dict:
        filters = filters or {}
        with self.db.session_scope() as session:
            query = select(Robot)
            if filters.get("q"):
                safe_q = escape_like_wildcards(filters["q"])
                query = query.where((Robot.name.ilike(f"%{safe_q}%", escape="\\")) | (Robot.robot_code.ilike(f"%{safe_q}%", escape="\\")))
            if filters.get("status"):
                query = query.where(Robot.status == filters["status"])
            total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
            robots = session.scalars(
                query.order_by(Robot.created_at.desc())
                .offset((filters["page"] - 1) * filters["page_size"])
                .limit(filters["page_size"])
            ).all()

            # Batch-load the most recent command for each robot (avoids N+1).
            robot_ids = [r.id for r in robots]
            recent_map = self._get_recent_commands_map(session, robot_ids) if robot_ids else {}

            return build_paginated_payload(
                [self.serialize_robot(robot, include_recent_command=False, recent_command=recent_map.get(robot.id)) for robot in robots],
                total,
                filters["page"],
                filters["page_size"],
            )

    def get_robot(self, robot_id: str) -> dict:
        with self.db.session_scope() as session:
            robot = session.get(Robot, robot_id)
            if not robot:
                raise ValueError("robot not found")
            heartbeat = session.scalar(
                select(RobotHeartbeat).where(RobotHeartbeat.robot_id == robot.id).order_by(desc(RobotHeartbeat.created_at))
            )
            data = self.serialize_robot(robot)
            data["last_heartbeat"] = (
                robot.last_heartbeat_at.isoformat() if robot.last_heartbeat_at else heartbeat.created_at.isoformat() if heartbeat else None
            )
            data["last_heartbeat_payload"] = heartbeat.payload if heartbeat else None
            return data

    def issue_command(self, robot_id: str, payload: dict, operator: str | None = None) -> dict:
        return self.command_service.issue_command(robot_id, payload, operator=operator)

    def list_commands(self, robot_id: str, filters: dict | None = None) -> dict:
        return self.command_service.list_commands(robot_id, filters)

    def resolve_robot_by_code(self, session, robot_code: str) -> Robot:
        robot = session.scalar(select(Robot).where(Robot.robot_code == robot_code))
        if not robot:
            raise ValueError(f"robot {robot_code} not found")
        return robot

    @staticmethod
    def _get_recent_commands_map(session, robot_ids: list[str]) -> dict[str, RobotCommand]:
        """Return {robot_id: most_recent_command} for the given robot IDs in one query."""
        if not robot_ids:
            return {}
        latest_subq = (
            select(
                RobotCommand.robot_id,
                func.max(RobotCommand.created_at).label("max_created"),
            )
            .where(RobotCommand.robot_id.in_(robot_ids))
            .group_by(RobotCommand.robot_id)
            .subquery()
        )
        rows = session.scalars(
            select(RobotCommand).join(
                latest_subq,
                (RobotCommand.robot_id == latest_subq.c.robot_id)
                & (RobotCommand.created_at == latest_subq.c.max_created),
            )
        ).all()
        return {cmd.robot_id: cmd for cmd in rows}

    def handle_heartbeat(self, robot_code: str, payload: dict) -> None:
        with self.db.session_scope() as session:
            try:
                self._validate_payload(payload, robot_code)
                robot = self.resolve_robot_by_code(session, robot_code)
                robot.status = payload.get("status", RobotStatus.ONLINE.value)
                robot.last_heartbeat_at = datetime.now(timezone.utc)
                session.add(RobotHeartbeat(robot_id=robot.id, status=robot.status, payload=payload))
                session.commit()
                self.realtime.publish("robot.heartbeat", {"robot_code": robot_code, "payload": payload})
            except Exception as exc:
                self.realtime.publish(
                    "system.alert",
                    {
                        "source": "robot_heartbeat",
                        "message": str(exc),
                        "robot_code": robot_code,
                        "payload": payload,
                    },
                )

    def handle_status(self, robot_code: str, payload: dict) -> None:
        with self.db.session_scope() as session:
            try:
                self._validate_payload(payload, robot_code)
                robot = self.resolve_robot_by_code(session, robot_code)
                robot.status = payload.get("status", RobotStatus.ONLINE.value)
                session.commit()
                self.realtime.publish("robot.status_changed", {"robot_code": robot_code, "payload": payload})
            except Exception as exc:
                self.realtime.publish(
                    "system.alert",
                    {
                        "source": "robot_status",
                        "message": str(exc),
                        "robot_code": robot_code,
                        "payload": payload,
                    },
                )

    def handle_command_event(self, robot_code: str, payload: dict) -> None:
        with self.db.session_scope() as session:
            try:
                self._validate_payload(payload, robot_code)
                command_id = payload.get("command_id")
                if not command_id:
                    raise ValueError("missing command_id")
                command = session.get(RobotCommand, command_id)
                if not command:
                    raise ValueError("command not found")
                robot = session.get(Robot, command.robot_id)
                if not robot or robot.robot_code != robot_code:
                    raise ValueError("robot-command mismatch")

                status = payload.get("status", RobotCommandStatus.ACKED.value)
                if status not in {item.value for item in RobotCommandStatus}:
                    raise ValueError("invalid command status")
                command.status = status
                command.result_json = payload.get("result", command.result_json or {})
                command.error_message = payload.get("error")
                if status in {RobotCommandStatus.COMPLETED.value, RobotCommandStatus.FAILED.value}:
                    command.completed_at = datetime.now(timezone.utc)

                robot_status = payload.get("robot_status")
                if robot_status:
                    robot.status = robot_status
                if command.command == "cancel_task" and command.params_json.get("task_id"):
                    task = session.get(Task, command.params_json["task_id"])
                    if task and task.robot_id == robot.id:
                        if status == RobotCommandStatus.COMPLETED.value:
                            task.status = TaskStateMachine.transition(TaskStatus(task.status), TaskStatus.CANCELLED).value
                            task.current_message = "任务已取消"
                            task.last_commanded_by = command.operator
                            session.add(
                                TaskEvent(
                                    task_id=task.id,
                                    robot_id=task.robot_id,
                                    event_type=TaskEventType.CANCELLED.value,
                                    payload={"command_id": command.id, "operator": command.operator},
                                )
                            )
                        elif status == RobotCommandStatus.FAILED.value:
                            task.status = TaskStatus.FAILED.value
                            task.failure_reason = payload.get("error") or "cancel task failed"
                session.commit()
                self.realtime.publish("robot.command_updated", self.serialize_command(command, robot))
                if command.command == "cancel_task" and command.params_json.get("task_id"):
                    task = session.get(Task, command.params_json["task_id"])
                    if task:
                        self.realtime.publish(
                            "task.updated",
                            {"task_id": task.id, "status": task.status, "message": task.current_message or task.status},
                        )
            except Exception as exc:
                self.realtime.publish(
                    "system.alert",
                    {
                        "source": "robot_command",
                        "message": str(exc),
                        "robot_code": robot_code,
                        "payload": payload,
                    },
                )

    def mark_stale_offline(self, ttl_seconds: int) -> int:
        with self.db.session_scope() as session:
            threshold = datetime.now(timezone.utc) - timedelta(seconds=ttl_seconds)
            robots = session.scalars(
                select(Robot).where(
                    Robot.last_heartbeat_at.is_not(None),
                    Robot.last_heartbeat_at < threshold,
                    Robot.status != RobotStatus.OFFLINE.value,
                )
            ).all()
            for robot in robots:
                robot.status = RobotStatus.OFFLINE.value
            session.commit()
            for robot in robots:
                self.realtime.publish(
                    "robot.status_changed",
                    {
                        "robot_code": robot.robot_code,
                        "payload": {"status": RobotStatus.OFFLINE.value, "reason": "heartbeat timeout"},
                    },
                )
            return len(robots)

    def serialize_robot(self, robot: Robot, include_recent_command: bool = True, recent_command: RobotCommand | None = None) -> dict:
        data = {
            "id": robot.id,
            "robot_code": robot.robot_code,
            "name": robot.name,
            "status": robot.status,
            "protocol": robot.protocol,
            "capabilities": robot.capabilities,
            "metadata": robot.metadata_json,
            "last_heartbeat_at": robot.last_heartbeat_at.isoformat() if robot.last_heartbeat_at else None,
            "created_at": robot.created_at.isoformat(),
            "updated_at": robot.updated_at.isoformat(),
        }
        if include_recent_command:
            if recent_command is None:
                with self.db.session_scope() as session:
                    recent_command = session.scalar(
                        select(RobotCommand).where(RobotCommand.robot_id == robot.id).order_by(desc(RobotCommand.created_at))
                    )
            data["recent_command"] = self.serialize_command(recent_command, robot) if recent_command else None
        return data

    @staticmethod
    def serialize_command(command: RobotCommand | None, robot: Robot | None = None) -> dict | None:
        return RobotCommandService.serialize_command(command, robot)

    @staticmethod
    def _validate_payload(payload: dict, robot_code: str) -> None:
        protocol_version = payload.get("protocol_version", "1.0")
        if protocol_version != "1.0":
            raise ValueError(f"unsupported protocol version from {robot_code}: {protocol_version}")

    @staticmethod
    def _validate_robot_registration(session, payload: dict) -> None:
        for field in ("robot_code", "name"):
            if not payload.get(field):
                raise ValueError(f"{field} is required")
        capabilities = payload.get("capabilities", {})
        metadata = payload.get("metadata", {})
        if not isinstance(capabilities, dict):
            raise ValueError("capabilities must be an object")
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be an object")
        existing = session.scalar(select(Robot).where(Robot.robot_code == payload["robot_code"]))
        if existing:
            raise ValueError("robot_code already exists")
