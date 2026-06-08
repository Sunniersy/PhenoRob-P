from pathlib import Path

from flask import g
from sqlalchemy import inspect

from backend.app.infra.db import DatabaseManager
from backend.app.infra.realtime import RealtimeBroker
from backend.app.infra.storage import create_storage
from backend.app.infra.task_queue import create_task_queue
from backend.app.infra.transport.factory import create_transport
from backend.app.models import Base
from backend.app.services.analysis_service import AnalysisService
from backend.app.services.auth_service import AuthService
from backend.app.services.admin_service import AdminService
from backend.app.services.asset_service import AssetService
from backend.app.services.dashboard_service import DashboardService
from backend.app.services.download_token_service import DownloadTokenService
from backend.app.services.result_service import ResultService
from backend.app.services.robot_service import RobotService
from backend.app.services.system_service import SystemService
from backend.app.services.task_service import TaskService


def bootstrap_extensions(app) -> None:
    Path(app.config["LOCAL_STORAGE_PATH"]).mkdir(parents=True, exist_ok=True)

    db = DatabaseManager(app.config["DATABASE_URL"])
    if app.config["TESTING"]:
        db.create_all(Base.metadata)
    realtime = RealtimeBroker(db=db, enabled=app.config["WEBSOCKET_ENABLED"])
    storage = create_storage(app.config)
    task_queue = create_task_queue(app.config)
    transport = create_transport(app.config)

    app.extensions["db"] = db
    app.extensions["realtime"] = realtime
    app.extensions["storage"] = storage
    app.extensions["task_queue"] = task_queue
    app.extensions["transport"] = transport

    auth_service = AuthService(db, app.config)
    admin_service = AdminService(db, app.config)
    robot_service = RobotService(db, realtime, transport)
    analysis_service = AnalysisService(db, storage, realtime, app.config)
    result_service = ResultService(db, task_queue)
    asset_service = AssetService(db, storage, task_queue, realtime)
    task_service = TaskService(db, transport, realtime, result_service, app.config)
    dashboard_service = DashboardService(db)
    system_service = SystemService(db, storage, task_queue, transport, realtime, app.config)
    system_service.app_version = app.config["APP_VERSION"]

    download_token_service = DownloadTokenService(
        redis_url=app.config.get("REDIS_URL"),
        ttl_seconds=app.config.get("DOWNLOAD_TOKEN_TTL", 600),
    )

    app.extensions["auth_service"] = auth_service
    app.extensions["admin_service"] = admin_service
    app.extensions["robot_service"] = robot_service
    app.extensions["analysis_service"] = analysis_service
    app.extensions["result_service"] = result_service
    app.extensions["asset_service"] = asset_service
    app.extensions["task_service"] = task_service
    app.extensions["dashboard_service"] = dashboard_service
    app.extensions["system_service"] = system_service
    app.extensions["download_token_service"] = download_token_service

    asset_service.bind_analysis_service(analysis_service)
    task_service.bind_robot_service(robot_service)
    task_queue.bind_analysis_callback(analysis_service.run_analysis)
    transport.bind_handlers(robot_service, task_service)

    inspector = inspect(db.engine)
    if inspector.has_table("roles"):
        auth_service.ensure_roles()


def teardown_extensions(app, exception=None) -> None:
    db = app.extensions.get("db")
    if db and hasattr(g, "db_session"):
        db.close_session(g.db_session)
