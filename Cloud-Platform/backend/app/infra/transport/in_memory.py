from shared.mqtt import TopicFactory

from .base import RobotTransport


class InMemoryTransport(RobotTransport):
    def __init__(self):
        self.dispatched_messages = []
        self.command_messages = []

    def publish_task(self, robot_code: str, payload: dict) -> None:
        self.dispatched_messages.append({"topic": TopicFactory.task_dispatch(robot_code), "payload": payload})

    def publish_command(self, robot_code: str, payload: dict) -> None:
        self.command_messages.append({"topic": TopicFactory.robot_command(robot_code), "payload": payload})

    def emit_heartbeat(self, robot_code: str, payload: dict) -> None:
        self.robot_service.handle_heartbeat(robot_code, payload)

    def emit_status(self, robot_code: str, payload: dict) -> None:
        self.robot_service.handle_status(robot_code, payload)

    def emit_progress(self, robot_code: str, payload: dict) -> None:
        self.task_service.handle_progress(robot_code, payload)

    def emit_ack(self, robot_code: str, payload: dict) -> None:
        self.task_service.handle_ack(robot_code, payload)

    def emit_event(self, robot_code: str, payload: dict) -> None:
        self.task_service.handle_exception_event(robot_code, payload)

    def emit_command_event(self, robot_code: str, payload: dict) -> None:
        self.robot_service.handle_command_event(robot_code, payload)

    def describe(self) -> dict:
        return {
            "backend": "memory",
            "pending_dispatches": len(self.dispatched_messages),
            "pending_commands": len(self.command_messages),
        }

    def healthcheck(self) -> dict:
        return self.describe()
