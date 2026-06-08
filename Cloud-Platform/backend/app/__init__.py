import json
import logging
import time
import uuid

from flask import Flask, g, request
from werkzeug.exceptions import HTTPException

from backend.app.errors import ApiError
from backend.app.cli import register_cli
from backend.app.config import Config
from backend.app.extensions import bootstrap_extensions, teardown_extensions
from backend.app.rate_limit import clear_limiters, init_limiter, init_named_limiter
from backend.app.routes import register_blueprints
from backend.app.routes.utils import api_response
from backend.app.routes.ws import register_ws


def create_app(config_object=None) -> Flask:
    app = Flask(__name__)
    config_cls = config_object or Config
    app.config.from_object(config_cls())
    _configure_logging(app)

    bootstrap_extensions(app)

    # Initialise rate limiters (skipped when RATE_LIMIT_LOGIN_ENABLED is false).
    if app.config.get("RATE_LIMIT_LOGIN_ENABLED", True):
        init_limiter(
            max_requests=app.config.get("RATE_LIMIT_LOGIN_MAX", 10),
            window_seconds=app.config.get("RATE_LIMIT_LOGIN_WINDOW", 300),
        )
        init_named_limiter(
            "refresh",
            max_requests=app.config.get("RATE_LIMIT_REFRESH_MAX", 20),
            window_seconds=app.config.get("RATE_LIMIT_REFRESH_WINDOW", 60),
        )
        init_named_limiter(
            "create_user",
            max_requests=app.config.get("RATE_LIMIT_CREATE_USER_MAX", 10),
            window_seconds=app.config.get("RATE_LIMIT_CREATE_USER_WINDOW", 60),
        )
    else:
        clear_limiters()

    register_blueprints(app)
    register_ws(app)
    register_cli(app)

    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = app.make_default_options_response()
            response.headers["Access-Control-Allow-Origin"] = app.config["FRONTEND_BASE_URL"]
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Bootstrap-Token"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            return response

    @app.before_request
    def begin_request():
        g.request_id = str(uuid.uuid4())
        g.request_started_at = time.time()

    @app.after_request
    def add_request_headers(response):
        response.headers["X-Request-ID"] = getattr(g, "request_id", "")
        duration_ms = int((time.time() - getattr(g, "request_started_at", time.time())) * 1000)
        app.logger.info(
            json.dumps(
                {
                    "request_id": getattr(g, "request_id", ""),
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                },
                ensure_ascii=False,
            )
        )
        return response

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = app.config["FRONTEND_BASE_URL"]
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-Bootstrap-Token"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        return response

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        teardown_extensions(app, exception)

    @app.errorhandler(ApiError)
    def handle_api_error(exc):
        return api_response(None, exc.message, exc.status_code, errors=exc.errors)

    @app.errorhandler(ValueError)
    def handle_value_error(exc):
        # 生产环境下不暴露详细的内部错误信息
        message = str(exc)
        # 过滤可能包含敏感信息的错误
        sensitive_patterns = [
            "not found", "duplicate", "constraint", "unique",
            "password", "secret", "token", "key", "credential",
            "sql", "database", "connection", "timeout"
        ]
        if any(pattern in message.lower() for pattern in sensitive_patterns):
            # 返回通用错误信息
            if "not found" in message.lower():
                return api_response(None, "请求的资源不存在", 404)
            return api_response(None, "请求处理失败", 400)
        # 在开发环境下返回详细信息，生产环境下返回通用信息
        if app.config.get("APP_ENV") == "development":
            return api_response(None, message, 400)
        return api_response(None, "请求处理失败", 400)

    @app.errorhandler(404)
    def handle_not_found(exc):
        return api_response(None, "请求的资源不存在", 404)

    @app.errorhandler(413)
    def handle_request_entity_too_large(exc):
        return api_response(None, "upload payload too large", 413)

    @app.errorhandler(Exception)
    def handle_exception(exc):
        if isinstance(exc, HTTPException):
            return api_response(None, exc.description, exc.code)
        return api_response(None, "internal server error", 500)

    return app


def _configure_logging(app: Flask) -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    app.logger.setLevel(logging.INFO)
