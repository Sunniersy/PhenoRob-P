import time

from sqlalchemy import case, func, select

from backend.app.models import AnalysisResult, DataAsset, Robot, SystemAlert, Task

# Simple TTL cache: {key: (value, timestamp)}
_cache: dict[str, tuple] = {}
_DEFAULT_TTL = 5  # seconds


def _get_cached(key: str, ttl_seconds: int = _DEFAULT_TTL):
    """Return cached value if still valid, otherwise None."""
    entry = _cache.get(key)
    if entry is None:
        return None
    value, ts = entry
    if time.monotonic() - ts > ttl_seconds:
        return None
    return value


def _set_cached(key: str, value) -> None:
    """Store value in cache with current timestamp."""
    _cache[key] = (value, time.monotonic())


class DashboardService:
    def __init__(self, db):
        self.db = db

    def overview(self) -> dict:
        cached = _get_cached("dashboard_overview")
        if cached is not None:
            return cached

        session = self.db.session()
        try:
            # Merge multiple COUNT queries into a single query using CASE WHEN
            counts = session.execute(
                select(
                    func.count().label("task_total"),
                    func.count(case((Task.status.in_(["DISPATCHED", "ROBOT_ACKED", "RUNNING"]), 1))).label(
                        "running_task_total"
                    ),
                )
            ).one()
            task_total = counts[0] or 0
            running_task_total = counts[1] or 0

            # Merge robot counts into a single query
            robot_counts = session.execute(
                select(
                    func.count().label("robot_total"),
                    func.count(case((Robot.status.in_(["ONLINE", "BUSY"]), 1))).label("robot_online"),
                )
            ).one()
            robot_total = robot_counts[0] or 0
            robot_online = robot_counts[1] or 0

            # Merge result and asset counts into a single query
            misc_counts = session.execute(
                select(
                    func.count().label("result_total"),
                ).select_from(AnalysisResult)
            ).one()
            result_total = misc_counts[0] or 0

            asset_total = session.scalar(select(func.count()).select_from(DataAsset)) or 0

            tasks = session.scalars(select(Task).order_by(Task.created_at.desc()).limit(5)).all()
            results = session.scalars(select(AnalysisResult).order_by(AnalysisResult.created_at.desc()).limit(5)).all()
            assets = session.scalars(select(DataAsset).order_by(DataAsset.created_at.desc()).limit(6)).all()
            alerts = session.scalars(select(SystemAlert).order_by(SystemAlert.created_at.desc()).limit(5)).all()

            result = {
                "task_total": task_total,
                "running_task_total": running_task_total,
                "robot_total": robot_total,
                "robot_online": robot_online,
                "result_total": result_total,
                "asset_total": asset_total,
                "recent_tasks": [{"id": item.id, "name": item.name, "status": item.status} for item in tasks],
                "recent_results": [{"task_id": item.task_id, "summary": item.summary} for item in results],
                "recent_assets": [
                    {
                        "id": item.id,
                        "task_id": item.task_id,
                        "robot_id": item.robot_id,
                        "file_name": item.file_name,
                        "asset_type": item.asset_type,
                        "created_at": item.created_at.isoformat(),
                    }
                    for item in assets
                ],
                "recent_alerts": [
                    {"id": item.id, "source": item.source, "message": item.message, "created_at": item.created_at.isoformat()}
                    for item in alerts
                ],
            }

            _set_cached("dashboard_overview", result)
            return result
        finally:
            session.close()
