from dataclasses import dataclass


class BaseTaskQueue:
    def bind_analysis_callback(self, callback):
        self._analysis_callback = callback

    def submit_analysis(self, task_id: str) -> None:
        raise NotImplementedError

    def describe(self) -> dict:
        raise NotImplementedError

    def healthcheck(self) -> dict:
        raise NotImplementedError


@dataclass
class InlineTaskQueue(BaseTaskQueue):
    eager: bool = True

    def submit_analysis(self, task_id: str) -> None:
        self._analysis_callback(task_id)

    def describe(self) -> dict:
        return {"backend": "inline", "eager": self.eager}

    def healthcheck(self) -> dict:
        return {"backend": "inline", "eager": self.eager}


class CeleryTaskQueue(BaseTaskQueue):
    def __init__(self, redis_url: str):
        from celery import Celery

        self.redis_url = redis_url
        self.celery = Celery("phenobot", broker=redis_url, backend=redis_url)

    def submit_analysis(self, task_id: str) -> None:
        self.celery.send_task("phenobot.analysis", args=[task_id])

    def describe(self) -> dict:
        return {"backend": "celery"}

    def healthcheck(self) -> dict:
        from redis import Redis

        client = Redis.from_url(self.redis_url)
        try:
            client.ping()
            return {"backend": "celery", "connectivity": "ok", "broker": self.redis_url}
        finally:
            client.close()


def create_task_queue(config: dict) -> BaseTaskQueue:
    if config["TASK_QUEUE_BACKEND"] == "celery":
        try:
            return CeleryTaskQueue(config["REDIS_URL"])
        except Exception:
            if not config["ALLOW_RUNTIME_FALLBACK"]:
                raise
    return InlineTaskQueue(eager=config["TASK_QUEUE_EAGER"])
