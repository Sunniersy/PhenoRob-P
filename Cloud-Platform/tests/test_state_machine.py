import pytest

from shared.enums import TaskStatus
from shared.mqtt import TopicFactory
from shared.state_machine import TaskStateMachine, TaskStateTransitionError


def test_task_state_machine_valid_path():
    status = TaskStatus.DRAFT
    for next_status in [
        TaskStatus.PENDING_DISPATCH,
        TaskStatus.DISPATCHED,
        TaskStatus.ROBOT_ACKED,
        TaskStatus.RUNNING,
        TaskStatus.DATA_UPLOADING,
        TaskStatus.DATA_READY,
        TaskStatus.ANALYZING,
        TaskStatus.COMPLETED,
    ]:
        status = TaskStateMachine.transition(status, next_status)
    assert status == TaskStatus.COMPLETED


def test_task_state_machine_invalid_transition():
    with pytest.raises(TaskStateTransitionError):
        TaskStateMachine.transition(TaskStatus.DRAFT, TaskStatus.COMPLETED)


def test_task_state_machine_retry_transitions():
    assert TaskStateMachine.transition(TaskStatus.FAILED, TaskStatus.PENDING_DISPATCH) == TaskStatus.PENDING_DISPATCH
    assert TaskStateMachine.transition(TaskStatus.FAILED, TaskStatus.DATA_READY) == TaskStatus.DATA_READY


def test_topic_factory():
    assert TopicFactory.task_dispatch("robot-001") == "greenhouse/tasks/robot-001/dispatch"
    assert TopicFactory.robot_progress("robot-001") == "greenhouse/robots/robot-001/progress"
