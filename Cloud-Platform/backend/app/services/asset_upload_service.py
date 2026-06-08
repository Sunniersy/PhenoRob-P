import hashlib
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy import select

from backend.app.models import DataAsset, Task, TaskEvent, UploadSession
from shared.enums import TaskEventType, TaskStatus
from shared.state_machine import TaskStateMachine

logger = logging.getLogger(__name__)


class AssetUploadService:
    def __init__(self, db, storage, task_queue, realtime):
        self.db = db
        self.storage = storage
        self.task_queue = task_queue
        self.realtime = realtime

    def create_upload_session(self, payload: dict) -> dict:
        with self.db.session_scope() as session:
            task = session.get(Task, payload["task_id"])
            if not task:
                raise ValueError("task not found")
            object_key = f"tasks/{task.id}/{payload['asset_type'].lower()}/{payload['file_name']}"
            existing_session = session.scalar(
                select(UploadSession).where(
                    UploadSession.task_id == task.id,
                    UploadSession.asset_type == payload["asset_type"],
                    UploadSession.object_key == object_key,
                )
            )
            if existing_session:
                return {
                    "upload_session_id": existing_session.id,
                    "task_id": task.id,
                    "object_key": existing_session.object_key,
                    "asset_type": existing_session.asset_type,
                    "storage": self.storage.describe(),
                    "idempotent": True,
                }

            current_status = TaskStatus(task.status)
            if current_status == TaskStatus.DATA_UPLOADING:
                pass  # Already in upload state
            elif TaskStateMachine.can_transition(current_status, TaskStatus.DATA_UPLOADING):
                task.status = TaskStateMachine.transition(current_status, TaskStatus.DATA_UPLOADING).value
            else:
                raise ValueError(f"task is not ready for upload session: {task.status}")

            upload_session = UploadSession(
                task_id=task.id,
                robot_id=task.robot_id,
                asset_type=payload["asset_type"],
                object_key=object_key,
            )
            session.add(upload_session)
            session.add(
                TaskEvent(
                    task_id=task.id,
                    robot_id=task.robot_id,
                    event_type=TaskEventType.DATA_SESSION_CREATED.value,
                    payload={"object_key": object_key, "asset_type": payload["asset_type"]},
                )
            )
            session.commit()
            logger.info(json.dumps({
                "event": "upload_session_created",
                "task_id": task.id,
                "upload_session_id": upload_session.id,
                "asset_type": payload["asset_type"],
                "object_key": object_key,
            }, ensure_ascii=False))
            self.realtime.publish(
                "task.updated",
                {"task_id": task.id, "status": task.status, "message": "上传会话已创建"},
            )
            return {
                "upload_session_id": upload_session.id,
                "task_id": task.id,
                "object_key": object_key,
                "asset_type": upload_session.asset_type,
                "storage": self.storage.describe(),
            }

    def complete_upload(self, payload: dict) -> dict:
        with self.db.session_scope() as session:
            try:
                upload_session = session.get(UploadSession, payload["upload_session_id"])
                if not upload_session:
                    raise ValueError("upload session not found")
                if "sha256" not in payload:
                    raise ValueError("sha256 is required")

                content = payload.get("content", "{}").encode("utf-8")
                content_sha256 = hashlib.sha256(content).hexdigest()
                if payload["sha256"] != content_sha256:
                    raise ValueError("sha256 mismatch")

                existing = session.scalar(
                    select(DataAsset).where(
                        DataAsset.upload_session_id == upload_session.id,
                        DataAsset.sha256 == payload["sha256"],
                    )
                )
                if existing:
                    return self._asset_response(existing, idempotent=True)
                if upload_session.status == "COMPLETED" and upload_session.sha256 and upload_session.sha256 != payload["sha256"]:
                    raise ValueError("upload session already completed with a different sha256")

                should_mark_failed = False
                storage_meta = self.storage.upload_bytes(upload_session.object_key, content)
                should_mark_failed = True
                upload_session.status = "COMPLETED"
                upload_session.completed_at = datetime.now(timezone.utc)
                upload_session.sha256 = payload["sha256"]

                asset = DataAsset(
                    task_id=upload_session.task_id,
                    robot_id=upload_session.robot_id,
                    upload_session_id=upload_session.id,
                    asset_type=upload_session.asset_type,
                    file_name=payload["file_name"],
                    object_key=upload_session.object_key,
                    sha256=payload["sha256"],
                    size_bytes=payload.get("size_bytes", storage_meta["size_bytes"]),
                    metadata_json=payload.get("metadata", {}),
                )
                session.add(asset)

                task = session.get(Task, upload_session.task_id)
                self._mark_task_data_ready(session, task)
                self._add_data_uploaded_event(session, task, upload_session)
                session.commit()
                logger.info(json.dumps({
                    "event": "upload_completed",
                    "task_id": task.id,
                    "upload_session_id": upload_session.id,
                    "asset_type": upload_session.asset_type,
                    "sha256": payload["sha256"],
                }, ensure_ascii=False))
                self.realtime.publish(
                    "task.updated",
                    {"task_id": task.id, "status": task.status, "message": task.current_message},
                )
                if payload.get("trigger_analysis", True):
                    self.task_queue.submit_analysis(task.id)
                return self._asset_response(asset)
            except Exception as exc:
                session.rollback()
                if locals().get("should_mark_failed") and "upload_session" in locals() and upload_session:
                    self._mark_upload_failed(session, upload_session, exc)
                raise

    def upload_session_content(self, upload_session_id: str, file_name: str, content: bytes) -> dict:
        with self.db.session_scope() as session:
            upload_session = session.get(UploadSession, upload_session_id)
            if not upload_session:
                raise ValueError("upload session not found")
            if file_name:
                upload_session.object_key = f"tasks/{upload_session.task_id}/{upload_session.asset_type.lower()}/{file_name}"
            upload_session.sha256 = hashlib.sha256(content).hexdigest()
            upload_session.status = "UPLOADED"
            storage_meta = self.storage.upload_bytes(upload_session.object_key, content)
            session.commit()
            return {
                "upload_session_id": upload_session.id,
                "status": upload_session.status,
                "object_key": upload_session.object_key,
                "sha256": upload_session.sha256,
                "size_bytes": storage_meta["size_bytes"],
            }

    def complete_uploaded_session(self, upload_session_id: str, metadata: dict | None = None, trigger_analysis: bool = True) -> dict:
        with self.db.session_scope() as session:
            upload_session = session.get(UploadSession, upload_session_id)
            if not upload_session:
                raise ValueError("upload session not found")
            if upload_session.status not in {"UPLOADED", "COMPLETED"}:
                raise ValueError("upload content has not been staged")

            existing = session.scalar(select(DataAsset).where(DataAsset.upload_session_id == upload_session.id))
            if existing:
                return self._asset_response(existing, idempotent=True)

            content = self.storage.get_bytes(upload_session.object_key)
            sha256 = hashlib.sha256(content).hexdigest()
            if upload_session.sha256 and upload_session.sha256 != sha256:
                raise ValueError("staged content sha256 mismatch")

            upload_session.status = "COMPLETED"
            upload_session.completed_at = datetime.now(timezone.utc)
            upload_session.sha256 = sha256
            task = session.get(Task, upload_session.task_id)
            self._mark_task_data_ready(session, task)

            file_name = Path(upload_session.object_key).name
            asset = DataAsset(
                task_id=upload_session.task_id,
                robot_id=upload_session.robot_id,
                upload_session_id=upload_session.id,
                asset_type=upload_session.asset_type,
                file_name=file_name,
                object_key=upload_session.object_key,
                sha256=sha256,
                size_bytes=len(content),
                metadata_json=metadata or {},
            )
            session.add(asset)
            self._add_data_uploaded_event(session, task, upload_session)
            session.commit()
            self.realtime.publish("task.updated", {"task_id": task.id, "status": task.status, "message": task.current_message})
            if trigger_analysis:
                self.task_queue.submit_analysis(task.id)
            return self._asset_response(asset)

    @staticmethod
    def _asset_response(asset: DataAsset, idempotent: bool = False) -> dict:
        data = {
            "asset_id": asset.id,
            "task_id": asset.task_id,
            "object_key": asset.object_key,
            "sha256": asset.sha256,
            "size_bytes": asset.size_bytes,
        }
        if idempotent:
            data["idempotent"] = True
        return data

    @staticmethod
    def _mark_task_data_ready(session, task: Task) -> None:
        current_status = TaskStatus(task.status)
        if current_status in {TaskStatus.DATA_READY, TaskStatus.ANALYZING, TaskStatus.COMPLETED}:
            # Already in a later state, no transition needed
            return
        if TaskStateMachine.can_transition(current_status, TaskStatus.DATA_READY):
            task.status = TaskStateMachine.transition(current_status, TaskStatus.DATA_READY).value
        task.current_message = "数据上传完成，等待分析"

    @staticmethod
    def _add_data_uploaded_event(session, task: Task, upload_session: UploadSession) -> None:
        session.add(
            TaskEvent(
                task_id=task.id,
                robot_id=task.robot_id,
                event_type=TaskEventType.DATA_UPLOADED.value,
                payload={
                    "upload_session_id": upload_session.id,
                    "object_key": upload_session.object_key,
                    "asset_type": upload_session.asset_type,
                },
            )
        )

    def _mark_upload_failed(self, session, upload_session: UploadSession, exc: Exception) -> None:
        task = session.get(Task, upload_session.task_id)
        if not task:
            return
        current_status = TaskStatus(task.status)
        if TaskStateMachine.can_transition(current_status, TaskStatus.FAILED):
            task.status = TaskStateMachine.transition(current_status, TaskStatus.FAILED).value
        task.current_message = "数据上传失败"
        session.add(
            TaskEvent(
                task_id=task.id,
                robot_id=task.robot_id,
                event_type=TaskEventType.EXCEPTION.value,
                payload={"error": str(exc), "stage": "complete_upload"},
            )
        )
        session.commit()
        logger.error(json.dumps({
            "event": "upload_failed",
            "task_id": task.id,
            "upload_session_id": upload_session.id,
            "error": str(exc),
        }, ensure_ascii=False))
        self.realtime.publish(
            "system.alert",
            {
                "source": "asset_upload",
                "message": "上传完成处理失败",
                "task_id": task.id,
                "error": str(exc),
            },
        )
