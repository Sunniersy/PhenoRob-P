import json
import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, selectinload

from backend.app.errors import NotFoundError
from backend.app.models import AnalysisJob, AnalysisResult, DataAsset, Robot, Task, TaskEvent, UploadSession
from backend.app.pagination import build_paginated_payload
from backend.app.services.task_dispatch_service import TaskDispatchService
from backend.app.validators import escape_like_wildcards
from shared.enums import AnalysisJobStatus, TaskEventType, TaskStatus
from shared.state_machine import TaskStateMachine

logger = logging.getLogger(__name__)


class TaskService:
    def __init__(self, db, transport, realtime, result_service, config):
        self.db = db
        self.transport = transport
        self.realtime = realtime
        self.result_service = result_service
        self.config = config
        self.robot_service = None
        self.dispatch_service = TaskDispatchService(db, transport, realtime, self.get_task)

    def bind_robot_service(self, robot_service):
        self.robot_service = robot_service

    def create_task(self, payload: dict, user_id: str | None = None) -> dict:
        with self.db.session_scope() as session:
            robot = session.get(Robot, payload["robot_id"])
            if not robot:
                raise ValueError("robot not found")
            task = Task(
                name=payload["name"],
                task_type=payload["task_type"],
                robot_id=robot.id,
                priority=payload.get("priority", 5),
                parameters_json=payload.get("parameters", {}),
                config_snapshot={
                    "task_type": payload["task_type"],
                    "parameters": payload.get("parameters", {}),
                    "robot_code": robot.robot_code,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
                created_by=user_id,
            )
            session.add(task)
            session.flush()
            session.add(TaskEvent(task_id=task.id, robot_id=task.robot_id, event_type=TaskEventType.CREATED.value, payload={}))
            task.status = TaskStateMachine.transition(TaskStatus.DRAFT, TaskStatus.PENDING_DISPATCH).value
            session.commit()
            logger.info(json.dumps({
                "event": "task_created",
                "task_id": task.id,
                "robot_id": task.robot_id,
                "task_type": task.task_type,
                "user_id": user_id,
                "status": task.status,
            }, ensure_ascii=False))
            return self.serialize_task(session, task)

    def list_tasks(self, filters: dict | None = None) -> dict:
        filters = filters or {}
        with self.db.session_scope() as session:
            # Use selectinload for N+1 query optimization
            query = select(Task).options(
                joinedload(Task.robot),
                selectinload(Task.analysis_jobs),
                selectinload(Task.analysis_results),
                selectinload(Task.data_assets),
                selectinload(Task.upload_sessions),
            )
            if filters.get("q"):
                safe_q = escape_like_wildcards(filters["q"])
                query = query.where(Task.name.ilike(f"%{safe_q}%", escape="\\"))
            if filters.get("status"):
                query = query.where(Task.status == filters["status"])
            # Count filtered tasks
            count_query = select(func.count()).select_from(Task)
            if filters.get("q"):
                safe_q = escape_like_wildcards(filters["q"])
                count_query = count_query.where(Task.name.ilike(f"%{safe_q}%", escape="\\"))
            if filters.get("status"):
                count_query = count_query.where(Task.status == filters["status"])
            total = session.scalar(count_query) or 0
            tasks = session.scalars(
                query.order_by(Task.created_at.desc())
                .offset((filters["page"] - 1) * filters["page_size"])
                .limit(filters["page_size"])
            ).unique().all()
            return build_paginated_payload(
                [self.serialize_task(session, task) for task in tasks], total, filters["page"], filters["page_size"]
            )

    def get_task(self, task_id: str) -> dict:
        with self.db.session_scope() as session:
            task = session.get(Task, task_id)
            if not task:
                raise NotFoundError("task")
            return self.serialize_task(session, task, include_timeline=True)

    def dispatch_task(self, task_id: str) -> dict:
        logger.info(json.dumps({
            "event": "task_dispatch",
            "task_id": task_id,
            "status": "dispatching",
        }, ensure_ascii=False))
        return self.dispatch_service.dispatch_task(task_id)

    def handle_ack(self, robot_code: str, payload: dict) -> None:
        """Handle task acknowledgment from robot."""
        task_id = payload.get("task_id")
        if not task_id:
            return
        with self.db.session_scope() as session:
            task = session.get(Task, task_id)
            if task:
                # First transition to ROBOT_ACKED, then to RUNNING
                task.status = TaskStateMachine.transition(TaskStatus(task.status), TaskStatus.ROBOT_ACKED).value
                task.status = TaskStateMachine.transition(TaskStatus(task.status), TaskStatus.RUNNING).value
                task.current_message = "任务执行中"
                session.add(
                    TaskEvent(
                        task_id=task.id,
                        robot_id=task.robot_id,
                        event_type=TaskEventType.ROBOT_ACK.value,
                        payload=payload,
                    )
                )
                session.commit()
                logger.info(json.dumps({
                    "event": "task_ack",
                    "task_id": task_id,
                    "robot_code": robot_code,
                }, ensure_ascii=False))

    def handle_progress(self, robot_code: str, payload: dict) -> None:
        """Handle task progress update from robot."""
        task_id = payload.get("task_id")
        progress = payload.get("progress", 0)
        if not task_id:
            return
        with self.db.session_scope() as session:
            task = session.get(Task, task_id)
            if task:
                task.progress = progress
                session.add(
                    TaskEvent(
                        task_id=task.id,
                        robot_id=task.robot_id,
                        event_type=TaskEventType.PROGRESS.value,
                        payload=payload,
                    )
                )
                session.commit()
                logger.info(json.dumps({
                    "event": "task_progress",
                    "task_id": task_id,
                    "robot_code": robot_code,
                    "progress": progress,
                }, ensure_ascii=False))

    def handle_exception_event(self, robot_code: str, payload: dict) -> None:
        """Handle task exception event from robot."""
        task_id = payload.get("task_id")
        if not task_id:
            return
        with self.db.session_scope() as session:
            task = session.get(Task, task_id)
            if task:
                task.status = TaskStatus.FAILED.value
                task.failure_reason = payload.get("error", "Unknown error")
                session.add(
                    TaskEvent(
                        task_id=task.id,
                        robot_id=task.robot_id,
                        event_type=TaskEventType.EXCEPTION.value,
                        payload=payload,
                    )
                )
                session.commit()
                logger.info(json.dumps({
                    "event": "task_exception",
                    "task_id": task_id,
                    "robot_code": robot_code,
                    "error": payload.get("error"),
                }, ensure_ascii=False))

    def retry_task(self, task_id: str) -> dict:
        with self.db.session_scope() as session:
            task = session.get(Task, task_id)
            if not task:
                raise ValueError("task not found")
            if TaskStatus(task.status) != TaskStatus.FAILED:
                raise ValueError("only failed tasks can be retried")
            analysis_job = session.scalar(select(AnalysisJob).where(AnalysisJob.task_id == task.id))
            mode = "dispatch"
            if analysis_job and analysis_job.status == AnalysisJobStatus.FAILED.value:
                mode = "analysis"
                task.status = TaskStateMachine.transition(TaskStatus.FAILED, TaskStatus.DATA_READY).value
                task.current_message = "重新提交分析"
            else:
                task.status = TaskStateMachine.transition(TaskStatus.FAILED, TaskStatus.PENDING_DISPATCH).value
                task.current_message = "等待重新下发"
            task.failure_reason = None
            session.add(
                TaskEvent(
                    task_id=task.id,
                    robot_id=task.robot_id,
                    event_type=TaskEventType.RETRY_REQUESTED.value,
                    payload={"mode": mode},
                )
            )
            session.commit()
            logger.info(json.dumps({
                "event": "task_retry",
                "task_id": task.id,
                "retry_mode": mode,
                "status": task.status,
            }, ensure_ascii=False))
            self.realtime.publish("task.updated", {"task_id": task.id, "status": task.status, "message": task.current_message})
        if mode == "analysis":
            self.result_service.requeue_analysis(task_id)
        return self.get_task(task_id)

    def cancel_task(self, task_id: str, username: str) -> dict:
        with self.db.session_scope() as session:
            task = session.get(Task, task_id)
            if not task:
                raise ValueError("task not found")
            current_status = TaskStatus(task.status)

            if current_status in {TaskStatus.CANCELLED, TaskStatus.COMPLETED}:
                raise ValueError("task cannot be cancelled")

            if current_status in {TaskStatus.DRAFT, TaskStatus.PENDING_DISPATCH, TaskStatus.FAILED}:
                task.status = TaskStateMachine.transition(current_status, TaskStatus.CANCELLED).value
                task.current_message = "任务已取消"
                task.last_commanded_by = username
                session.add(
                    TaskEvent(
                        task_id=task.id,
                        robot_id=task.robot_id,
                        event_type=TaskEventType.CANCELLED.value,
                        payload={"operator": username, "mode": "local"},
                    )
                )
                session.commit()
                logger.info(json.dumps({
                    "event": "task_cancel",
                    "task_id": task.id,
                    "operator": username,
                    "cancel_mode": "local",
                    "status": task.status,
                }, ensure_ascii=False))
                self.realtime.publish("task.updated", {"task_id": task.id, "status": task.status, "message": task.current_message})
                return self.serialize_task(session, task)

            if current_status == TaskStatus.CANCELLING:
                return self.serialize_task(session, task)

            if not self.robot_service:
                raise RuntimeError("robot service is not bound")

            self.robot_service.issue_command(
                task.robot_id,
                {"command": "cancel_task", "params": {"task_id": task.id}},
                operator=username,
            )
            task.status = TaskStateMachine.transition(current_status, TaskStatus.CANCELLING).value
            task.current_message = "取消指令已下发"
            task.last_commanded_by = username
            session.add(
                TaskEvent(
                    task_id=task.id,
                    robot_id=task.robot_id,
                    event_type=TaskEventType.CANCELLED.value,
                    payload={"operator": username, "mode": "remote"},
                )
            )
            session.commit()
            logger.info(json.dumps({
                "event": "task_cancel",
                "task_id": task.id,
                "operator": username,
                "cancel_mode": "remote",
                "status": task.status,
            }, ensure_ascii=False))
            self.realtime.publish("task.updated", {"task_id": task.id, "status": task.status, "message": task.current_message})
            return self.serialize_task(session, task)

    def serialize_task(self, session, task, include_timeline: bool = False) -> dict:
        # Use preloaded relationships if available, otherwise query
        result = task.analysis_results[0] if hasattr(task, 'analysis_results') and task.analysis_results else None
        if not result:
            result = session.scalar(select(AnalysisResult).where(AnalysisResult.task_id == task.id))

        analysis_job = task.analysis_jobs[0] if hasattr(task, 'analysis_jobs') and task.analysis_jobs else None
        if not analysis_job:
            analysis_job = session.scalar(select(AnalysisJob).where(AnalysisJob.task_id == task.id))

        assets = task.data_assets if hasattr(task, 'data_assets') and task.data_assets is not None else None
        if assets is None:
            assets = session.scalars(select(DataAsset).where(DataAsset.task_id == task.id)).all()

        upload_sessions = task.upload_sessions if hasattr(task, 'upload_sessions') and task.upload_sessions is not None else None
        if upload_sessions is None:
            upload_sessions = session.scalars(select(UploadSession).where(UploadSession.task_id == task.id)).all()

        payload = {
            "id": task.id,
            "name": task.name,
            "task_type": task.task_type,
            "robot_id": task.robot_id,
            "robot_code": task.robot.robot_code if task.robot else None,
            "status": task.status,
            "progress": task.progress or 0,
            "priority": task.priority,
            "current_message": task.current_message,
            "failure_reason": task.failure_reason,
            "parameters": task.parameters_json or {},
            "config_snapshot": task.config_snapshot or {},
            "created_by": task.created_by,
            "last_commanded_by": task.last_commanded_by,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "result_ready": result is not None,
            "analysis_status": analysis_job.status if analysis_job else "DISABLED",
            "analysis_result": {
                "id": result.id,
                "summary": result.summary,
                "result_object_key": result.result_object_key,
                "created_at": result.created_at.isoformat() if result.created_at else None,
            } if result else None,
            "analysis_job": {
                "id": analysis_job.id,
                "status": analysis_job.status,
                "provider": analysis_job.provider,
                "retry_count": analysis_job.retry_count,
                "created_at": analysis_job.created_at.isoformat() if analysis_job.created_at else None,
            } if analysis_job else None,
            "assets": [
                {
                    "id": asset.id,
                    "asset_type": asset.asset_type,
                    "file_name": asset.file_name,
                    "size_bytes": asset.size_bytes,
                    "created_at": asset.created_at.isoformat() if asset.created_at else None,
                }
                for asset in assets
            ],
            "upload_sessions": [
                {
                    "id": us.id,
                    "status": us.status,
                    "asset_type": us.asset_type,
                    "object_key": us.object_key,
                    "created_at": us.created_at.isoformat() if us.created_at else None,
                }
                for us in upload_sessions
            ],
        }

        if include_timeline:
            events = session.scalars(
                select(TaskEvent)
                .where(TaskEvent.task_id == task.id)
                .order_by(TaskEvent.created_at.asc())
            ).all()
            payload["timeline"] = [
                {
                    "id": event.id,
                    "event_type": event.event_type,
                    "payload": event.payload,
                    "created_at": event.created_at.isoformat() if event.created_at else None,
                }
                for event in events
            ]

        return payload
