from sqlalchemy import func, select

from backend.app.models import AnalysisJob, AnalysisResult
from backend.app.pagination import build_paginated_payload
from backend.app.validators import escape_like_wildcards


class ResultService:
    def __init__(self, db, task_queue=None):
        self.db = db
        self.task_queue = task_queue

    def list_results(self, filters: dict | None = None) -> dict:
        filters = filters or {}
        with self.db.session_scope() as session:
            query = select(AnalysisResult)
            if filters.get("q"):
                query = query.where(AnalysisResult.summary.ilike(f"%{escape_like_wildcards(filters['q'])}%"))
            total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
            results = session.scalars(
                query.order_by(AnalysisResult.created_at.desc())
                .offset((filters["page"] - 1) * filters["page_size"])
                .limit(filters["page_size"])
            ).all()
            return build_paginated_payload(
                [self.serialize_result(item) for item in results], total, filters["page"], filters["page_size"]
            )

    def get_result_by_task(self, task_id: str) -> dict | None:
        with self.db.session_scope() as session:
            item = session.scalar(select(AnalysisResult).where(AnalysisResult.task_id == task_id))
            return self.serialize_result(item) if item else None

    @staticmethod
    def serialize_result(item: AnalysisResult) -> dict:
        return {
            "id": item.id,
            "task_id": item.task_id,
            "summary": item.summary,
            "result_json": item.result_json,
            "result_object_key": item.result_object_key,
            "created_at": item.created_at.isoformat(),
        }

    def requeue_analysis(self, task_id: str) -> None:
        with self.db.session_scope() as session:
            job = session.scalar(select(AnalysisJob).where(AnalysisJob.task_id == task_id))
            if job:
                job.status = "PENDING"
                job.error_message = None
                session.commit()
        if not self.task_queue:
            raise RuntimeError("task queue is not configured for requeue")
        self.task_queue.submit_analysis(task_id)
