import hashlib
import shutil
import uuid
from pathlib import Path

import pytest
from sqlalchemy import select

from backend.app import create_app
from backend.app.config import TestingConfig
from backend.app.models import AnalysisJob, AnalysisResult, DataAsset, Task, TaskEvent
from shared.enums import AnalysisJobStatus, TaskEventType, TaskStatus


# ---------------------------------------------------------------------------
# Config & fixtures for demo-provider tests
# ---------------------------------------------------------------------------

class DemoAnalysisConfig(TestingConfig):
    ANALYSIS_PROVIDER = "demo"
    ANALYSIS_LATENCY_SECONDS = 0
    LOCAL_STORAGE_PATH = "storage/test/analysis-svc"


@pytest.fixture()
def demo_app():
    storage_dir = Path(DemoAnalysisConfig.LOCAL_STORAGE_PATH)
    if storage_dir.exists():
        shutil.rmtree(storage_dir)
    application = create_app(DemoAnalysisConfig)
    yield application
    if storage_dir.exists():
        shutil.rmtree(storage_dir)


@pytest.fixture()
def demo_client(demo_app):
    return demo_app.test_client()


@pytest.fixture()
def demo_auth(demo_client):
    resp = demo_client.post(
        "/api/auth/bootstrap-admin",
        json={"username": "admin", "password": "super-secret123"},
    )
    return {"Authorization": f"Bearer {resp.get_json()['data']['token']}"}


@pytest.fixture()
def demo_robot(demo_client, demo_auth):
    return demo_client.post(
        "/api/robots/register",
        headers=demo_auth,
        json={
            "robot_code": "robot-analysis-001",
            "name": "Analysis Robot",
            "protocol": "mqtt",
            "capabilities": {"sensors": ["rgb"]},
            "metadata": {},
        },
    ).get_json()["data"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_task(client, headers, robot_id, name="analysis-task"):
    return client.post(
        "/api/tasks",
        headers=headers,
        json={
            "name": name,
            "task_type": "phenotyping_capture",
            "robot_id": robot_id,
            "parameters": {},
        },
    ).get_json()["data"]


def _add_asset(db, task_id, robot_id, file_name="capture.json"):
    session = db.session()
    try:
        session.add(
            DataAsset(
                task_id=task_id,
                robot_id=robot_id,
                asset_type="IMAGE",
                file_name=file_name,
                object_key=f"tasks/{task_id}/image/{file_name}",
                sha256=hashlib.sha256(file_name.encode()).hexdigest(),
                size_bytes=512,
                metadata_json={},
            )
        )
        session.commit()
    finally:
        session.close()


def _set_status(db, task_id, status):
    session = db.session()
    try:
        session.get(Task, task_id).status = status.value
        session.commit()
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Test 1 -- demo provider normal flow
# ---------------------------------------------------------------------------

def test_demo_provider_normal_flow(demo_app, demo_client, demo_auth, demo_robot):
    """Demo provider result_json contains all expected fields and task reaches COMPLETED."""
    task = _create_task(demo_client, demo_auth, demo_robot["id"])
    db = demo_app.extensions["db"]
    _add_asset(db, task["id"], demo_robot["id"])
    _set_status(db, task["id"], TaskStatus.DATA_READY)

    demo_app.extensions["analysis_service"].run_analysis(task["id"])

    session = db.session()
    try:
        result = session.scalar(
            select(AnalysisResult).where(AnalysisResult.task_id == task["id"])
        )
        assert result is not None
        rj = result.result_json
        assert rj["provider"] == "demo"
        assert rj["task_id"] == task["id"]
        assert rj["task_name"] == "analysis-task"
        assert rj["asset_count"] == 1
        assert rj["latest_asset"]["file_name"] == "capture.json"
        assert "generated_at" in rj
        assert "Demo 分析完成" in result.summary

        job = session.scalar(
            select(AnalysisJob).where(AnalysisJob.task_id == task["id"])
        )
        assert job.status == AnalysisJobStatus.SUCCESS.value
        assert job.provider == "demo"

        assert session.get(Task, task["id"]).status == TaskStatus.COMPLETED.value
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Test 2 -- disabled provider
# ---------------------------------------------------------------------------

def test_disabled_provider_skips_analysis(app, client, auth_headers, robot):
    """Disabled provider skips analysis, sets message, and creates skipped event."""
    task = _create_task(client, auth_headers, robot["id"])
    db = app.extensions["db"]
    _set_status(db, task["id"], TaskStatus.DATA_READY)

    app.extensions["analysis_service"].run_analysis(task["id"])

    session = db.session()
    try:
        t = session.get(Task, task["id"])
        assert t.current_message == "数据上传完成，未配置分析服务"

        assert (
            session.scalar(
                select(AnalysisResult).where(AnalysisResult.task_id == task["id"])
            )
            is None
        )

        evt = session.scalar(
            select(TaskEvent).where(
                TaskEvent.task_id == task["id"],
                TaskEvent.event_type == TaskEventType.ANALYSIS_FINISHED.value,
            )
        )
        assert evt is not None
        assert evt.payload["skipped"] is True
        assert evt.payload["provider"] == "disabled"
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Test 3 -- analysis failure
# ---------------------------------------------------------------------------

def test_analysis_failure_marks_task_and_job_failed(
    demo_app, demo_client, demo_auth, demo_robot, monkeypatch
):
    """Provider exception transitions task to FAILED and sets AnalysisJob to FAILED."""
    task = _create_task(demo_client, demo_auth, demo_robot["id"])
    db = demo_app.extensions["db"]
    _add_asset(db, task["id"], demo_robot["id"])
    _set_status(db, task["id"], TaskStatus.DATA_READY)

    svc = demo_app.extensions["analysis_service"]

    def _boom(t, a):
        raise RuntimeError("provider exploded")

    monkeypatch.setattr(svc, "_run_provider", _boom)

    with pytest.raises(RuntimeError, match="provider exploded"):
        svc.run_analysis(task["id"])

    session = db.session()
    try:
        t = session.get(Task, task["id"])
        assert t.status == TaskStatus.FAILED.value
        assert t.current_message == "分析失败"
        assert "provider exploded" in t.failure_reason

        job = session.scalar(
            select(AnalysisJob).where(AnalysisJob.task_id == task["id"])
        )
        assert job.status == AnalysisJobStatus.FAILED.value
        assert "provider exploded" in job.error_message

        evt = session.scalar(
            select(TaskEvent).where(
                TaskEvent.task_id == task["id"],
                TaskEvent.event_type == TaskEventType.ANALYSIS_FAILED.value,
            )
        )
        assert evt is not None
        assert "provider exploded" in evt.payload["error"]
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Test 4 -- duplicate analysis (update, not duplicate)
# ---------------------------------------------------------------------------

def test_rerun_updates_existing_result(demo_app, demo_client, demo_auth, demo_robot):
    """Re-running analysis updates the existing AnalysisResult instead of creating a duplicate."""
    task = _create_task(demo_client, demo_auth, demo_robot["id"], name="rerun-task")
    db = demo_app.extensions["db"]
    _add_asset(db, task["id"], demo_robot["id"])

    # Pre-create stale result and job to simulate a previous run
    session = db.session()
    try:
        session.add(
            AnalysisResult(
                task_id=task["id"],
                summary="stale summary",
                result_json={"provider": "demo", "stale": True},
                result_object_key=f"results/{task['id']}/analysis.json",
            )
        )
        session.add(
            AnalysisJob(
                task_id=task["id"],
                provider="demo",
                status=AnalysisJobStatus.SUCCESS.value,
                retry_count=1,
            )
        )
        session.commit()
    finally:
        session.close()

    _set_status(db, task["id"], TaskStatus.DATA_READY)
    demo_app.extensions["analysis_service"].run_analysis(task["id"])

    session = db.session()
    try:
        results = session.scalars(
            select(AnalysisResult).where(AnalysisResult.task_id == task["id"])
        ).all()
        assert len(results) == 1
        assert "stale" not in results[0].result_json
        assert results[0].result_json["provider"] == "demo"
        assert results[0].summary == "Demo 分析完成，共处理 1 个数据资产。"

        job = session.scalar(
            select(AnalysisJob).where(AnalysisJob.task_id == task["id"])
        )
        assert job.retry_count == 2
        assert job.error_message is None
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Test 5 -- task not found
# ---------------------------------------------------------------------------

def test_nonexistent_task_raises_value_error(demo_app):
    """Running analysis on a non-existent task_id raises ValueError."""
    with pytest.raises(ValueError, match="task not found"):
        demo_app.extensions["analysis_service"].run_analysis(str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# Test 6 -- state machine verification
# ---------------------------------------------------------------------------

def test_state_transitions_during_analysis(demo_app, demo_client, demo_auth, demo_robot):
    """Verify DATA_READY -> ANALYZING -> COMPLETED transitions via task events."""
    task = _create_task(demo_client, demo_auth, demo_robot["id"], name="sm-task")
    db = demo_app.extensions["db"]
    _add_asset(db, task["id"], demo_robot["id"])
    _set_status(db, task["id"], TaskStatus.DATA_READY)

    demo_app.extensions["analysis_service"].run_analysis(task["id"])

    session = db.session()
    try:
        assert session.get(Task, task["id"]).status == TaskStatus.COMPLETED.value

        events = (
            session.scalars(
                select(TaskEvent)
                .where(TaskEvent.task_id == task["id"])
                .order_by(TaskEvent.created_at)
            )
        ).all()
        event_types = [e.event_type for e in events]

        assert TaskEventType.ANALYSIS_STARTED.value in event_types
        assert TaskEventType.ANALYSIS_FINISHED.value in event_types
        assert event_types.index(TaskEventType.ANALYSIS_STARTED.value) < event_types.index(
            TaskEventType.ANALYSIS_FINISHED.value
        )

        started_evt = [
            e for e in events if e.event_type == TaskEventType.ANALYSIS_STARTED.value
        ][0]
        assert started_evt.payload["provider"] == "demo"
    finally:
        session.close()
