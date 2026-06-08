from datetime import datetime, timezone
from typing import Callable

from backend.app.errors import UpstreamError
from backend.app.models import Robot, Task, TaskEvent
from shared.enums import TaskEventType, TaskStatus
from shared.state_machine import TaskStateMachine


class TaskDispatchService:
    def __init__(self, db, transport, realtime, get_task: Callable[[str], dict]):
        self.db = db
        self.transport = transport
        self.realtime = realtime
        self.get_task = get_task

    def dispatch_task(self, task_id: str) -> dict:
        session = self.db.session()
        try:
            task = session.get(Task, task_id)
            if not task:
                raise ValueError("task not found")
            robot = session.get(Robot, task.robot_id)
            self._validate_dispatch(task)
            payload = self._build_dispatch_payload(task, robot)
            task.current_message = "任务下发中"
            task.status = TaskStateMachine.transition(TaskStatus(task.status), TaskStatus.DISPATCHED).value
            task.current_message = "任务已下发"
            session.add(
                TaskEvent(
                    task_id=task.id,
                    robot_id=task.robot_id,
                    event_type=TaskEventType.DISPATCHED.value,
                    payload=payload,
                )
            )
            session.commit()  # commit to DB before publishing MQTT
            try:
                self.transport.publish_task(robot.robot_code, payload)
            except Exception as exc:
                session2 = self.db.session()
                try:
                    task2 = session2.get(Task, task_id)
                    if task2:
                        task2.status = TaskStatus.FAILED.value
                        task2.current_message = "任务下发失败"
                        task2.failure_reason = str(exc)
                        session2.commit()
                finally:
                    session2.close()
                raise UpstreamError("task dispatch failed", errors={"detail": str(exc)}) from exc
            self.realtime.publish("task.updated", {"task_id": task.id, "status": task.status, "message": task.current_message})
            return self.get_task(task_id)
        finally:
            session.close()

    @staticmethod
    def _build_dispatch_payload(task: Task, robot: Robot) -> dict:
        return {
            "message_id": f"dispatch-{task.id}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "robot_id": robot.robot_code,
            "task_id": task.id,
            "event_type": "dispatch",
            "protocol_version": "1.0",
            "payload": {
                "task_name": task.name,
                "task_type": task.task_type,
                "priority": task.priority,
                "parameters": task.parameters_json,
            },
        }

    @staticmethod
    def _validate_dispatch(task: Task) -> None:
        if TaskStatus(task.status) != TaskStatus.PENDING_DISPATCH:
            raise ValueError("task is not ready for dispatch")
