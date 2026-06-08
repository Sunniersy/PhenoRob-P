from dataclasses import dataclass

from .enums import TaskStatus


class TaskStateTransitionError(ValueError):
    pass


@dataclass(frozen=True)
class TaskTransition:
    source: TaskStatus
    target: TaskStatus


class TaskStateMachine:
    _allowed = {
        TaskStatus.DRAFT: {TaskStatus.PENDING_DISPATCH, TaskStatus.CANCELLED},
        TaskStatus.PENDING_DISPATCH: {TaskStatus.DISPATCHED, TaskStatus.CANCELLED},
        TaskStatus.DISPATCHED: {TaskStatus.ROBOT_ACKED, TaskStatus.FAILED, TaskStatus.CANCELLING, TaskStatus.CANCELLED},
        TaskStatus.ROBOT_ACKED: {TaskStatus.RUNNING, TaskStatus.FAILED, TaskStatus.CANCELLING, TaskStatus.CANCELLED},
        TaskStatus.RUNNING: {TaskStatus.DATA_UPLOADING, TaskStatus.FAILED, TaskStatus.CANCELLING, TaskStatus.CANCELLED},
        TaskStatus.DATA_UPLOADING: {TaskStatus.DATA_READY, TaskStatus.FAILED, TaskStatus.CANCELLING, TaskStatus.CANCELLED},
        TaskStatus.DATA_READY: {TaskStatus.ANALYZING, TaskStatus.FAILED, TaskStatus.CANCELLING, TaskStatus.CANCELLED},
        TaskStatus.ANALYZING: {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLING},
        TaskStatus.CANCELLING: {TaskStatus.CANCELLED, TaskStatus.FAILED},
        TaskStatus.COMPLETED: set(),
        TaskStatus.FAILED: {TaskStatus.PENDING_DISPATCH, TaskStatus.DATA_READY, TaskStatus.CANCELLED},
        TaskStatus.CANCELLED: set(),
    }

    @classmethod
    def can_transition(cls, current: TaskStatus, target: TaskStatus) -> bool:
        return target in cls._allowed[current]

    @classmethod
    def transition(cls, current: TaskStatus, target: TaskStatus) -> TaskStatus:
        if target not in cls._allowed[current]:
            raise TaskStateTransitionError(f"invalid transition: {current} -> {target}")
        return target
