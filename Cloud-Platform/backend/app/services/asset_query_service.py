import mimetypes
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from backend.app.models import AnalysisResult, DataAsset, Robot, Task
from backend.app.pagination import build_paginated_payload
from backend.app.validators import escape_like_wildcards


class AssetQueryService:
    def __init__(self, db, storage):
        self.db = db
        self.storage = storage

    def list_assets(self, filters: dict | None = None) -> dict:
        filters = filters or {}
        with self.db.session_scope() as session:
            query = select(DataAsset)
            if filters.get("q"):
                query = query.where(DataAsset.file_name.ilike(f"%{escape_like_wildcards(filters['q'])}%"))
            if filters.get("task_id"):
                query = query.where(DataAsset.task_id == filters["task_id"])
            if filters.get("robot_id"):
                query = query.where(DataAsset.robot_id == filters["robot_id"])
            if filters.get("asset_type"):
                query = query.where(DataAsset.asset_type == filters["asset_type"])
            if filters.get("date_from"):
                query = query.where(DataAsset.created_at >= datetime.fromisoformat(filters["date_from"]))
            if filters.get("date_to"):
                query = query.where(DataAsset.created_at <= datetime.fromisoformat(filters["date_to"]))

            total = session.scalar(select(func.count()).select_from(query.subquery())) or 0

            # Eagerly load task, robot, and analysis_result to avoid N+1 queries.
            query = query.options(
                joinedload(DataAsset.task),
                joinedload(DataAsset.robot),
                joinedload(DataAsset.analysis_result),
            )

            assets = session.scalars(
                query.order_by(DataAsset.created_at.desc())
                .offset((filters["page"] - 1) * filters["page_size"])
                .limit(filters["page_size"])
            ).unique().all()

            return build_paginated_payload(
                [self.serialize_asset(session, item) for item in assets], total, filters["page"], filters["page_size"]
            )

    def get_asset(self, asset_id: str) -> dict:
        with self.db.session_scope() as session:
            asset = session.get(DataAsset, asset_id)
            if not asset:
                raise ValueError("asset not found")
            return self.serialize_asset(session, asset, include_preview=True)

    def download_asset(self, asset_id: str) -> dict:
        with self.db.session_scope() as session:
            asset = session.get(DataAsset, asset_id)
            if not asset:
                raise ValueError("asset not found")
            return {
                "asset": self.serialize_asset(session, asset, include_preview=True),
                "content": self.storage.get_bytes(asset.object_key),
                "content_type": mimetypes.guess_type(asset.file_name)[0] or "application/octet-stream",
            }

    @staticmethod
    def serialize_asset(session, asset: DataAsset, include_preview: bool = False) -> dict:
        # Relationships are eagerly loaded in list_assets(); for single-item
        # endpoints the session is still open so lazy loading works transparently.
        task = asset.task
        robot = asset.robot
        result = asset.analysis_result
        data = {
            "id": asset.id,
            "task_id": asset.task_id,
            "task_name": task.name if task else None,
            "robot_id": asset.robot_id,
            "robot_code": robot.robot_code if robot else None,
            "robot_name": robot.name if robot else None,
            "asset_type": asset.asset_type,
            "file_name": asset.file_name,
            "object_key": asset.object_key,
            "sha256": asset.sha256,
            "size_bytes": asset.size_bytes,
            "metadata": asset.metadata_json,
            "created_at": asset.created_at.isoformat(),
            "result": {
                "task_id": result.task_id,
                "summary": result.summary,
                "result_object_key": result.result_object_key,
            }
            if result
            else None,
        }
        if include_preview:
            data["preview_path"] = f"/api/assets/{asset.id}/download"
        return data
