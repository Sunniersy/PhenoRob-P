import json
import logging
import time
from datetime import datetime, timezone

import requests
from sqlalchemy import select

from backend.app.errors import NotFoundError
from backend.app.models import AnalysisJob, AnalysisResult, DataAsset, Task, TaskEvent
from shared.enums import AnalysisJobStatus, TaskEventType, TaskStatus
from shared.state_machine import TaskStateMachine

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, db, storage, realtime, config):
        self.db = db
        self.storage = storage
        self.realtime = realtime
        self.config = config

    def run_analysis(self, task_id: str) -> None:
        if self.config["ANALYSIS_PROVIDER"] == "disabled":
            self._complete_without_analysis(task_id)
            return

        session = self.db.session()
        try:
            task = session.get(Task, task_id)
            if not task:
                raise ValueError("task not found")

            job = session.scalar(select(AnalysisJob).where(AnalysisJob.task_id == task_id))
            if not job:
                job = AnalysisJob(task_id=task_id, provider=self.config["ANALYSIS_PROVIDER"])
                session.add(job)
                session.flush()

            task.status = TaskStateMachine.transition(TaskStatus(task.status), TaskStatus.ANALYZING).value
            job.status = AnalysisJobStatus.RUNNING.value
            job.retry_count = (job.retry_count or 0) + 1
            job.error_message = None
            session.add(
                TaskEvent(
                    task_id=task.id,
                    robot_id=task.robot_id,
                    event_type=TaskEventType.ANALYSIS_STARTED.value,
                    payload={"provider": job.provider},
                )
            )
            session.commit()
            logger.info(json.dumps({
                "event": "analysis_started",
                "task_id": task.id,
                "provider": job.provider,
                "retry_count": job.retry_count,
            }, ensure_ascii=False))

            time.sleep(self.config["ANALYSIS_LATENCY_SECONDS"])
            assets = session.scalars(select(DataAsset).where(DataAsset.task_id == task_id)).all()
            result_json, summary = self._run_provider(task, assets)
            object_key = f"results/{task_id}/analysis.json"
            self.storage.upload_bytes(object_key, json.dumps(result_json, ensure_ascii=False, indent=2).encode("utf-8"))

            result = session.scalar(select(AnalysisResult).where(AnalysisResult.task_id == task_id))
            if not result:
                result = AnalysisResult(task_id=task_id, summary=summary, result_json=result_json, result_object_key=object_key)
                session.add(result)
            else:
                result.summary = summary
                result.result_json = result_json
                result.result_object_key = object_key

            job.status = AnalysisJobStatus.SUCCESS.value
            task.status = TaskStateMachine.transition(TaskStatus(task.status), TaskStatus.COMPLETED).value
            task.current_message = "分析完成"
            session.add(
                TaskEvent(
                    task_id=task.id,
                    robot_id=task.robot_id,
                    event_type=TaskEventType.ANALYSIS_FINISHED.value,
                    payload=result_json,
                )
            )
            session.commit()

            logger.info(json.dumps({
                "event": "analysis_completed",
                "task_id": task.id,
                "provider": job.provider,
                "asset_count": len(assets),
                "status": task.status,
            }, ensure_ascii=False))

            self.realtime.publish(
                "analysis.finished",
                {"task_id": task.id, "summary": summary, "result_object_key": object_key},
            )
            self.realtime.publish(
                "task.updated",
                {"task_id": task.id, "status": task.status, "message": task.current_message},
            )
        except Exception as exc:
            session.rollback()
            task = session.get(Task, task_id)
            job = session.scalar(select(AnalysisJob).where(AnalysisJob.task_id == task_id))
            if task:
                current_status = TaskStatus(task.status)
                if TaskStateMachine.can_transition(current_status, TaskStatus.FAILED):
                    task.status = TaskStateMachine.transition(current_status, TaskStatus.FAILED).value
                task.current_message = "分析失败"
                task.failure_reason = str(exc)
            if job:
                job.status = AnalysisJobStatus.FAILED.value
                job.error_message = str(exc)
            if task:
                session.add(
                    TaskEvent(
                        task_id=task_id,
                        robot_id=task.robot_id,
                        event_type=TaskEventType.ANALYSIS_FAILED.value,
                        payload={"error": str(exc)},
                    )
                )
            session.commit()

            logger.error(json.dumps({
                "event": "analysis_failed",
                "task_id": task_id,
                "error": str(exc),
            }, ensure_ascii=False))

            self.realtime.publish(
                "system.alert",
                {
                    "source": "analysis",
                    "message": "分析失败",
                    "task_id": task_id,
                    "error": str(exc),
                },
            )
            raise
        finally:
            session.close()

    def _run_provider(self, task: Task, assets: list[DataAsset]) -> tuple[dict, str]:
        provider = self.config["ANALYSIS_PROVIDER"]
        if provider == "demo":
            return self._run_demo_provider(task, assets)
        if provider == "http":
            return self._run_http_provider(task, assets)
        raise ValueError(f"unsupported analysis provider: {provider}")

    @staticmethod
    def _run_demo_provider(task: Task, assets: list[DataAsset]) -> tuple[dict, str]:
        asset_counts: dict[str, int] = {}
        for item in assets:
            asset_counts[item.asset_type] = asset_counts.get(item.asset_type, 0) + 1

        latest_asset = assets[-1] if assets else None
        result_json = {
            "provider": "demo",
            "task_id": task.id,
            "task_name": task.name,
            "task_type": task.task_type,
            "asset_count": len(assets),
            "asset_counts": asset_counts,
            "latest_asset": {
                "id": latest_asset.id,
                "file_name": latest_asset.file_name,
                "asset_type": latest_asset.asset_type,
            }
            if latest_asset
            else None,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        summary = f"Demo 分析完成，共处理 {len(assets)} 个数据资产。"
        return result_json, summary

    def _run_http_provider(self, task: Task, assets: list[DataAsset]) -> tuple[dict, str]:
        endpoint = self.config["ANALYSIS_HTTP_ENDPOINT"]
        headers = {"Content-Type": "application/json"}
        if self.config["ANALYSIS_HTTP_TOKEN"]:
            headers["Authorization"] = f"Bearer {self.config['ANALYSIS_HTTP_TOKEN']}"
        response = requests.post(
            endpoint,
            headers=headers,
            json={
                "task_id": task.id,
                "task_name": task.name,
                "task_type": task.task_type,
                "assets": [
                    {
                        "id": item.id,
                        "asset_type": item.asset_type,
                        "object_key": item.object_key,
                        "metadata": item.metadata_json,
                    }
                    for item in assets
                ],
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        result_json = payload.get("result") or payload
        summary = payload.get("summary") or f"HTTP 分析完成，共处理 {len(assets)} 个数据资产。"
        return result_json, summary

    def _complete_without_analysis(self, task_id: str) -> None:
        session = self.db.session()
        try:
            task = session.get(Task, task_id)
            if not task:
                raise NotFoundError("task")
            current_status = TaskStatus(task.status)
            # First transition to ANALYZING, then to COMPLETED
            if TaskStateMachine.can_transition(current_status, TaskStatus.ANALYZING):
                task.status = TaskStateMachine.transition(current_status, TaskStatus.ANALYZING).value
            if TaskStateMachine.can_transition(TaskStatus(task.status), TaskStatus.COMPLETED):
                task.status = TaskStateMachine.transition(TaskStatus(task.status), TaskStatus.COMPLETED).value
            task.current_message = "数据上传完成，未配置分析服务"
            session.add(
                TaskEvent(
                    task_id=task.id,
                    robot_id=task.robot_id,
                    event_type=TaskEventType.ANALYSIS_FINISHED.value,
                    payload={"provider": "disabled", "skipped": True},
                )
            )
            session.commit()
            self.realtime.publish(
                "task.updated",
                {"task_id": task.id, "status": task.status, "message": task.current_message},
            )
        finally:
            session.close()
