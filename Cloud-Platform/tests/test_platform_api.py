from io import BytesIO

import pytest

from backend.app import create_app
from backend.app.config import Config, TestingConfig as AppTestingConfig
from backend.app.infra.storage import LocalObjectStorage


def test_production_config_rejects_default_secrets():
    class UnsafeConfig(Config):
        APP_ENV = "production"
        DEBUG = False
        TESTING = False
        DATABASE_URL = "sqlite://"
        STORAGE_BACKEND = "local"
        TRANSPORT_BACKEND = "memory"
        TASK_QUEUE_BACKEND = "inline"
        TASK_QUEUE_EAGER = True
        LOCAL_STORAGE_PATH = "storage/test/unsafe-config"
        WEBSOCKET_ENABLED = False
        FRONTEND_BASE_URL = "http://localhost:5173"
        SECRET_KEY = "change-me"
        JWT_SECRET = "change-me-too"

    with pytest.raises(ValueError):
        create_app(UnsafeConfig)


def test_production_config_rejects_placeholder_release_secrets():
    class PlaceholderConfig(Config):
        APP_ENV = "production"
        DEBUG = False
        TESTING = False
        DATABASE_URL = "sqlite://"
        STORAGE_BACKEND = "local"
        TRANSPORT_BACKEND = "memory"
        TASK_QUEUE_BACKEND = "inline"
        TASK_QUEUE_EAGER = True
        LOCAL_STORAGE_PATH = "storage/test/placeholder-config"
        WEBSOCKET_ENABLED = False
        FRONTEND_BASE_URL = "https://robot-cloud.example.com"
        SECRET_KEY = "replace-with-a-strong-secret"
        JWT_SECRET = "replace-with-a-strong-jwt-secret"
        BOOTSTRAP_TOKEN = "replace-with-a-bootstrap-token"
        PASSWORD_MIN_LENGTH = 12

    with pytest.raises(ValueError, match="placeholder"):
        create_app(PlaceholderConfig)


def test_development_app_env_allows_default_local_bootstrap_values():
    class DevelopmentConfig(Config):
        APP_ENV = "development"
        DEBUG = False
        TESTING = False
        DATABASE_URL = "sqlite://"
        STORAGE_BACKEND = "local"
        TRANSPORT_BACKEND = "memory"
        TASK_QUEUE_BACKEND = "inline"
        TASK_QUEUE_EAGER = True
        LOCAL_STORAGE_PATH = "storage/test/dev-config"
        WEBSOCKET_ENABLED = False
        FRONTEND_BASE_URL = "http://localhost:5173"
        SECRET_KEY = "change-me"
        JWT_SECRET = "change-me-too"

    app = create_app(DevelopmentConfig)

    assert app.config["APP_ENV"] == "development"


def test_invalid_analysis_provider_is_rejected_early():
    class InvalidAnalysisConfig(Config):
        APP_ENV = "development"
        DEBUG = False
        TESTING = False
        DATABASE_URL = "sqlite://"
        STORAGE_BACKEND = "local"
        TRANSPORT_BACKEND = "memory"
        TASK_QUEUE_BACKEND = "inline"
        TASK_QUEUE_EAGER = True
        LOCAL_STORAGE_PATH = "storage/test/invalid-analysis-provider"
        WEBSOCKET_ENABLED = False
        FRONTEND_BASE_URL = "http://localhost:5173"
        SECRET_KEY = "change-me"
        JWT_SECRET = "change-me-too"
        ANALYSIS_PROVIDER = "nope"

    with pytest.raises(ValueError, match="ANALYSIS_PROVIDER"):
        create_app(InvalidAnalysisConfig)


def test_bootstrap_admin_requires_bootstrap_token_when_configured():
    class BootstrapTokenConfig(AppTestingConfig):
        BOOTSTRAP_TOKEN = "bootstrap-secret"
        LOCAL_STORAGE_PATH = "storage/test/bootstrap-token"

    app = create_app(BootstrapTokenConfig)
    client = app.test_client()

    denied = client.post("/api/auth/bootstrap-admin", json={"username": "admin", "password": "super-secret123"})
    assert denied.status_code == 401
    assert denied.get_json()["message"] == "invalid bootstrap token"

    allowed = client.post(
        "/api/auth/bootstrap-admin",
        headers={"X-Bootstrap-Token": "bootstrap-secret"},
        json={"username": "admin", "password": "super-secret123"},
    )
    assert allowed.status_code == 201


def test_bootstrap_admin_cors_headers_allow_bootstrap_token():
    response = client = create_app(AppTestingConfig).test_client().options("/api/auth/bootstrap-admin")

    assert response.status_code == 200
    allow_headers = response.headers["Access-Control-Allow-Headers"]
    assert "X-Bootstrap-Token" in allow_headers
    assert "Authorization" in allow_headers


def test_password_policy_uses_configured_minimum_length():
    class StrictPasswordConfig(AppTestingConfig):
        PASSWORD_MIN_LENGTH = 12
        LOCAL_STORAGE_PATH = "storage/test/strict-password"

    app = create_app(StrictPasswordConfig)
    client = app.test_client()

    weak = client.post("/api/auth/bootstrap-admin", json={"username": "admin", "password": "short123"})
    assert weak.status_code == 400
    assert weak.get_json()["errors"]["password"] == "密码长度至少为 12 位"

    strong = client.post("/api/auth/bootstrap-admin", json={"username": "admin", "password": "super-secret123"})
    assert strong.status_code == 201


def test_upload_content_rejects_file_over_max_upload_size():
    class SmallUploadConfig(AppTestingConfig):
        MAX_UPLOAD_SIZE_BYTES = 512
        LOCAL_STORAGE_PATH = "storage/test/small-upload"

    app = create_app(SmallUploadConfig)
    client = app.test_client()

    bootstrap = client.post("/api/auth/bootstrap-admin", json={"username": "admin", "password": "super-secret123"})
    headers = {"Authorization": f"Bearer {bootstrap.get_json()['data']['token']}"}
    robot = client.post(
        "/api/robots/register",
        headers=headers,
        json={
            "robot_code": "robot-oversize-01",
            "name": "上传限制机器人",
            "protocol": "mqtt",
            "capabilities": {"sensors": ["rgb"]},
            "metadata": {"zone": "qa"},
        },
    ).get_json()["data"]
    task = client.post(
        "/api/tasks",
        headers=headers,
        json={"name": "oversized-upload", "task_type": "phenotyping_capture", "robot_id": robot["id"], "parameters": {}},
    ).get_json()["data"]

    client.post(f"/api/tasks/{task['id']}/dispatch", headers=headers)
    app.extensions["transport"].emit_ack(robot["robot_code"], {"task_id": task["id"], "protocol_version": "1.0"})
    app.extensions["transport"].emit_progress(
        robot["robot_code"], {"task_id": task["id"], "progress": 50, "protocol_version": "1.0"}
    )
    session = client.post(
        "/api/assets/upload-sessions",
        headers=headers,
        json={"task_id": task["id"], "asset_type": "IMAGE", "file_name": "oversized.bin"},
    ).get_json()["data"]

    upload = client.put(
        f"/api/assets/upload-sessions/{session['upload_session_id']}/content",
        headers=headers,
        data={"file": (BytesIO(b"x" * 1024), "oversized.bin")},
        content_type="multipart/form-data",
    )
    assert upload.status_code == 413
    assert upload.get_json()["message"] == "upload payload too large"


def test_upload_session_rejects_path_traversal_file_name(client, auth_headers, robot):
    task = client.post(
        "/api/tasks",
        headers=auth_headers,
        json={"name": "traversal-upload", "task_type": "phenotyping_capture", "robot_id": robot["id"], "parameters": {}},
    ).get_json()["data"]
    client.post(f"/api/tasks/{task['id']}/dispatch", headers=auth_headers)
    client.application.extensions["transport"].emit_ack(robot["robot_code"], {"task_id": task["id"], "protocol_version": "1.0"})
    client.application.extensions["transport"].emit_progress(
        robot["robot_code"], {"task_id": task["id"], "progress": 50, "protocol_version": "1.0"}
    )

    response = client.post(
        "/api/assets/upload-sessions",
        headers=auth_headers,
        json={"task_id": task["id"], "asset_type": "IMAGE", "file_name": "../escape.bin"},
    )

    assert response.status_code == 400
    assert response.get_json()["errors"]["file_name"] == "文件名不能包含路径分隔符"


def test_upload_content_rejects_path_traversal_file_name(client, auth_headers, robot):
    task = client.post(
        "/api/tasks",
        headers=auth_headers,
        json={"name": "staged-traversal-upload", "task_type": "phenotyping_capture", "robot_id": robot["id"], "parameters": {}},
    ).get_json()["data"]
    client.post(f"/api/tasks/{task['id']}/dispatch", headers=auth_headers)
    client.application.extensions["transport"].emit_ack(robot["robot_code"], {"task_id": task["id"], "protocol_version": "1.0"})
    client.application.extensions["transport"].emit_progress(
        robot["robot_code"], {"task_id": task["id"], "progress": 50, "protocol_version": "1.0"}
    )
    session = client.post(
        "/api/assets/upload-sessions",
        headers=auth_headers,
        json={"task_id": task["id"], "asset_type": "IMAGE", "file_name": "safe.bin"},
    ).get_json()["data"]

    response = client.put(
        f"/api/assets/upload-sessions/{session['upload_session_id']}/content",
        headers=auth_headers,
        data={"file": (BytesIO(b"safe"), "../escape.bin")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.get_json()["errors"]["file_name"] == "文件名不能包含路径分隔符"


def test_local_storage_rejects_object_key_outside_base_path(tmp_path):
    storage = LocalObjectStorage(str(tmp_path / "objects"))

    with pytest.raises(ValueError, match="invalid object key"):
        storage.upload_bytes("../escape.bin", b"owned")

    assert not (tmp_path / "escape.bin").exists()


def test_bootstrap_check_reports_initial_admin_requirement(client, bootstrap_admin_payload):
    before = client.get("/api/system/bootstrap-check")
    assert before.status_code == 200
    before_payload = before.get_json()["data"]
    assert before_payload["needs_initial_admin"] is True
    assert before_payload["initialization_ok"] is False

    bootstrap = client.post("/api/auth/bootstrap-admin", json=bootstrap_admin_payload)
    assert bootstrap.status_code == 201

    after = client.get("/api/system/bootstrap-check")
    assert after.status_code == 200
    after_payload = after.get_json()["data"]
    assert after_payload["needs_initial_admin"] is False
    assert after_payload["initialization_ok"] is True


def test_auth_internal_error_is_not_reported_as_401(client, auth_headers, monkeypatch):
    def crash_current_user(token: str):
        raise RuntimeError("database session broke")

    monkeypatch.setattr(client.application.extensions["auth_service"], "current_user", crash_current_user)

    response = client.get("/api/tasks", headers=auth_headers)

    assert response.status_code == 500
    assert response.get_json()["message"] == "internal server error"


def test_task_list_returns_paginated_payload_and_supports_query_filters(client, auth_headers, robot):
    client.post(
        "/api/tasks",
        headers=auth_headers,
        json={"name": "alpha-capture", "task_type": "phenotyping_capture", "robot_id": robot["id"], "parameters": {}},
    )
    client.post(
        "/api/tasks",
        headers=auth_headers,
        json={"name": "beta-capture", "task_type": "phenotyping_capture", "robot_id": robot["id"], "parameters": {}},
    )

    response = client.get("/api/tasks?page=1&page_size=1&q=beta&status=PENDING_DISPATCH", headers=auth_headers)

    assert response.status_code == 200
    payload = response.get_json()["data"]
    assert payload["page"] == 1
    assert payload["page_size"] == 1
    assert payload["total"] == 1
    assert payload["items"][0]["name"] == "beta-capture"


def test_task_cancel_marks_pending_task_cancelled(client, auth_headers, robot):
    task = client.post(
        "/api/tasks",
        headers=auth_headers,
        json={"name": "cancel-me", "task_type": "phenotyping_capture", "robot_id": robot["id"], "parameters": {}},
    ).get_json()["data"]

    response = client.post(f"/api/tasks/{task['id']}/cancel", headers=auth_headers)

    assert response.status_code == 200
    payload = response.get_json()["data"]
    assert payload["status"] == "CANCELLED"
    assert payload["current_message"] == "任务已取消"


def test_runtime_endpoint_and_alert_ack_flow(client, auth_headers):
    client.application.extensions["realtime"].publish(
        "system.alert",
        {"source": "analysis", "level": "ERROR", "message": "analysis failed", "error": "boom"},
    )

    runtime = client.get("/api/system/runtime", headers=auth_headers)
    assert runtime.status_code == 200
    runtime_payload = runtime.get_json()["data"]
    assert "version" in runtime_payload
    assert runtime_payload["backends"]["storage"]["backend"] in {"local", "minio"}

    alerts = client.get("/api/system/alerts?level=ERROR&status=unread", headers=auth_headers)
    assert alerts.status_code == 200
    alerts_payload = alerts.get_json()["data"]
    assert alerts_payload["total"] >= 1
    alert_id = alerts_payload["items"][0]["id"]
    assert alerts_payload["items"][0]["is_acknowledged"] is False

    ack = client.patch(f"/api/system/alerts/{alert_id}/status", headers=auth_headers, json={"is_acknowledged": True})
    assert ack.status_code == 200
    assert ack.get_json()["data"]["is_acknowledged"] is True


def test_release_readiness_reports_production_blockers(client, auth_headers):
    response = client.get("/api/system/release-readiness", headers=auth_headers)

    assert response.status_code == 200
    payload = response.get_json()["data"]
    assert payload["ok"] is False

    checks = {item["key"]: item for item in payload["checks"]}
    assert checks["bootstrap_token"]["ok"] is False
    assert checks["frontend_origin_https"]["ok"] is False
    assert checks["analysis_provider"]["ok"] is False
    assert checks["password_policy"]["ok"] is False


def test_release_readiness_can_pass_for_hardened_runtime():
    class HardenedRuntimeConfig(AppTestingConfig):
        APP_ENV = "production"
        FRONTEND_BASE_URL = "https://robot-cloud.example.com"
        BOOTSTRAP_TOKEN = "bootstrap-secret"
        PASSWORD_MIN_LENGTH = 12
        ANALYSIS_PROVIDER = "http"
        ANALYSIS_HTTP_ENDPOINT = "https://analysis.example.com/v1/analyze"
        STORAGE_BACKEND = "minio"
        MINIO_ACCESS_KEY = "release-minio-user"
        MINIO_SECRET_KEY = "release-minio-secret-32"
        TASK_QUEUE_BACKEND = "celery"
        TRANSPORT_BACKEND = "mqtt"
        MQTT_USERNAME = "release-mqtt-user"
        MQTT_PASSWORD = "release-mqtt-password-32"
        WEBSOCKET_ENABLED = True
        LOCAL_STORAGE_PATH = "storage/test/hardened-runtime"

    app = create_app(HardenedRuntimeConfig)
    client = app.test_client()

    bootstrap = client.post(
        "/api/auth/bootstrap-admin",
        headers={"X-Bootstrap-Token": "bootstrap-secret"},
        json={"username": "admin", "password": "super-secret123"},
    )
    headers = {"Authorization": f"Bearer {bootstrap.get_json()['data']['token']}"}

    response = client.get("/api/system/release-readiness", headers=headers)

    assert response.status_code == 200
    payload = response.get_json()["data"]
    assert payload["ok"] is True
    assert all(item["ok"] for item in payload["checks"])


def test_release_readiness_blocks_missing_mqtt_credentials():
    class MissingMqttCredentialsConfig(AppTestingConfig):
        APP_ENV = "production"
        FRONTEND_BASE_URL = "https://robot-cloud.example.com"
        BOOTSTRAP_TOKEN = "bootstrap-secret"
        PASSWORD_MIN_LENGTH = 12
        ANALYSIS_PROVIDER = "http"
        ANALYSIS_HTTP_ENDPOINT = "https://analysis.example.com/v1/analyze"
        STORAGE_BACKEND = "minio"
        MINIO_ACCESS_KEY = "release-minio-user"
        MINIO_SECRET_KEY = "release-minio-secret-32"
        TASK_QUEUE_BACKEND = "celery"
        TRANSPORT_BACKEND = "mqtt"
        MQTT_USERNAME = ""
        MQTT_PASSWORD = ""
        WEBSOCKET_ENABLED = True
        LOCAL_STORAGE_PATH = "storage/test/missing-mqtt-credentials"

    app = create_app(MissingMqttCredentialsConfig)
    client = app.test_client()

    bootstrap = client.post(
        "/api/auth/bootstrap-admin",
        headers={"X-Bootstrap-Token": "bootstrap-secret"},
        json={"username": "admin", "password": "super-secret123"},
    )
    headers = {"Authorization": f"Bearer {bootstrap.get_json()['data']['token']}"}

    response = client.get("/api/system/release-readiness", headers=headers)

    checks = {item["key"]: item for item in response.get_json()["data"]["checks"]}
    assert checks["mqtt_credentials"]["ok"] is False
    assert response.get_json()["data"]["ok"] is False


def test_release_readiness_blocks_demo_application_secrets():
    class DemoSecretRuntimeConfig(AppTestingConfig):
        APP_ENV = "production"
        FRONTEND_BASE_URL = "https://robot-cloud.example.com"
        SECRET_KEY = "demo-secret-key-for-compose-only-32"
        JWT_SECRET = "demo-jwt-secret-key-for-compose-only-32"
        BOOTSTRAP_TOKEN = "demo-bootstrap-token-for-compose-only"
        PASSWORD_MIN_LENGTH = 12
        ANALYSIS_PROVIDER = "http"
        ANALYSIS_HTTP_ENDPOINT = "https://analysis.example.com/v1/analyze"
        STORAGE_BACKEND = "minio"
        MINIO_ACCESS_KEY = "release-minio-user"
        MINIO_SECRET_KEY = "release-minio-secret-32"
        TASK_QUEUE_BACKEND = "celery"
        TRANSPORT_BACKEND = "mqtt"
        WEBSOCKET_ENABLED = True
        LOCAL_STORAGE_PATH = "storage/test/demo-secret-runtime"

    app = create_app(DemoSecretRuntimeConfig)
    client = app.test_client()

    bootstrap = client.post(
        "/api/auth/bootstrap-admin",
        headers={"X-Bootstrap-Token": "demo-bootstrap-token-for-compose-only"},
        json={"username": "admin", "password": "super-secret123"},
    )
    headers = {"Authorization": f"Bearer {bootstrap.get_json()['data']['token']}"}

    response = client.get("/api/system/release-readiness", headers=headers)

    checks = {item["key"]: item for item in response.get_json()["data"]["checks"]}
    assert checks["application_secrets"]["ok"] is False
    assert response.get_json()["data"]["ok"] is False


def test_release_readiness_blocks_demo_minio_credentials():
    class DemoMinioRuntimeConfig(AppTestingConfig):
        APP_ENV = "production"
        FRONTEND_BASE_URL = "https://robot-cloud.example.com"
        BOOTSTRAP_TOKEN = "bootstrap-secret"
        PASSWORD_MIN_LENGTH = 12
        ANALYSIS_PROVIDER = "http"
        ANALYSIS_HTTP_ENDPOINT = "https://analysis.example.com/v1/analyze"
        STORAGE_BACKEND = "minio"
        MINIO_ACCESS_KEY = "demo-minio-root"
        MINIO_SECRET_KEY = "demo-minio-root-secret-32"
        TASK_QUEUE_BACKEND = "celery"
        TRANSPORT_BACKEND = "mqtt"
        MQTT_USERNAME = "release-mqtt-user"
        MQTT_PASSWORD = "release-mqtt-password-32"
        WEBSOCKET_ENABLED = True
        LOCAL_STORAGE_PATH = "storage/test/demo-minio-runtime"

    app = create_app(DemoMinioRuntimeConfig)
    client = app.test_client()

    bootstrap = client.post(
        "/api/auth/bootstrap-admin",
        headers={"X-Bootstrap-Token": "bootstrap-secret"},
        json={"username": "admin", "password": "super-secret123"},
    )
    headers = {"Authorization": f"Bearer {bootstrap.get_json()['data']['token']}"}

    response = client.get("/api/system/release-readiness", headers=headers)

    checks = {item["key"]: item for item in response.get_json()["data"]["checks"]}
    assert checks["minio_credentials"]["ok"] is False
    assert response.get_json()["data"]["ok"] is False


def test_reset_password_requires_new_password_to_login(client, auth_headers):
    created = client.post(
        "/api/users",
        headers=auth_headers,
        json={"username": "reset-user", "password": "secret123", "role": "operator"},
    )
    user_id = created.get_json()["data"]["id"]

    reset = client.post(
        f"/api/users/{user_id}/reset-password",
        headers=auth_headers,
        json={"password": "new-secret456"},
    )
    assert reset.status_code == 200
    assert reset.get_json()["data"]["must_change_password"] is False

    old_login = client.post("/api/auth/login", json={"username": "reset-user", "password": "secret123"})
    assert old_login.status_code == 401

    new_login = client.post("/api/auth/login", json={"username": "reset-user", "password": "new-secret456"})
    assert new_login.status_code == 200


def test_new_upload_flow_supports_binary_upload_and_explicit_complete(client, auth_headers, robot):
    task = client.post(
        "/api/tasks",
        headers=auth_headers,
        json={"name": "binary-upload", "task_type": "phenotyping_capture", "robot_id": robot["id"], "parameters": {}},
    ).get_json()["data"]
    client.post(f"/api/tasks/{task['id']}/dispatch", headers=auth_headers)
    client.application.extensions["transport"].emit_ack(robot["robot_code"], {"task_id": task["id"], "protocol_version": "1.0"})
    client.application.extensions["transport"].emit_progress(
        robot["robot_code"], {"task_id": task["id"], "progress": 50, "protocol_version": "1.0"}
    )

    session = client.post(
        "/api/assets/upload-sessions",
        headers=auth_headers,
        json={"task_id": task["id"], "asset_type": "IMAGE", "file_name": "binary.svg"},
    ).get_json()["data"]

    upload = client.put(
        f"/api/assets/upload-sessions/{session['upload_session_id']}/content",
        headers=auth_headers,
        data={"file": (BytesIO(b"<svg></svg>"), "binary.svg")},
        content_type="multipart/form-data",
    )
    assert upload.status_code == 200
    assert upload.get_json()["data"]["status"] == "UPLOADED"

    complete = client.post(
        f"/api/assets/upload-sessions/{session['upload_session_id']}/complete",
        headers=auth_headers,
        json={"metadata": {"source": "binary-test"}, "trigger_analysis": True},
    )
    assert complete.status_code == 201
    asset_payload = complete.get_json()["data"]
    assert asset_payload["asset_id"]


def test_response_contains_request_id_and_validation_errors(client, auth_headers):
    response = client.post("/api/tasks", headers=auth_headers, json={})

    assert response.status_code == 400
    payload = response.get_json()
    assert payload["request_id"]
    assert payload["errors"]["name"] == "任务名称不能为空"
