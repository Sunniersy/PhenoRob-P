class RobotTransport:
    def bind_handlers(self, robot_service, task_service) -> None:
        self.robot_service = robot_service
        self.task_service = task_service

    def publish_task(self, robot_code: str, payload: dict) -> None:
        raise NotImplementedError

    def publish_command(self, robot_code: str, payload: dict) -> None:
        raise NotImplementedError

    def describe(self) -> dict:
        raise NotImplementedError

    def healthcheck(self) -> dict:
        raise NotImplementedError
