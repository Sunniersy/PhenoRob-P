class TopicFactory:
    PREFIX = "greenhouse"

    @classmethod
    def robot_heartbeat(cls, robot_id: str) -> str:
        return f"{cls.PREFIX}/robots/{robot_id}/heartbeat"

    @classmethod
    def robot_status(cls, robot_id: str) -> str:
        return f"{cls.PREFIX}/robots/{robot_id}/status"

    @classmethod
    def robot_progress(cls, robot_id: str) -> str:
        return f"{cls.PREFIX}/robots/{robot_id}/progress"

    @classmethod
    def robot_events(cls, robot_id: str) -> str:
        return f"{cls.PREFIX}/robots/{robot_id}/events"

    @classmethod
    def robot_ack(cls, robot_id: str) -> str:
        return f"{cls.PREFIX}/robots/{robot_id}/ack"

    @classmethod
    def robot_data(cls, robot_id: str) -> str:
        return f"{cls.PREFIX}/robots/{robot_id}/data"

    @classmethod
    def robot_command(cls, robot_id: str) -> str:
        return f"{cls.PREFIX}/robots/{robot_id}/commands"

    @classmethod
    def robot_command_events(cls, robot_id: str) -> str:
        return f"{cls.PREFIX}/robots/{robot_id}/command-events"

    @classmethod
    def task_dispatch(cls, robot_id: str) -> str:
        return f"{cls.PREFIX}/tasks/{robot_id}/dispatch"

    @classmethod
    def task_control(cls, task_id: str) -> str:
        return f"{cls.PREFIX}/tasks/{task_id}/control"

    @classmethod
    def system_broadcast(cls) -> str:
        return f"{cls.PREFIX}/system/broadcast"
