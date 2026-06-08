from scripts import acceptance_smoke


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def json(self) -> dict:
        return self._payload


def test_build_settings_falls_back_to_simulator_defaults(monkeypatch):
    monkeypatch.delenv("BOOTSTRAP_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("BOOTSTRAP_ADMIN_PASSWORD", raising=False)
    monkeypatch.setenv("BOOTSTRAP_TOKEN", "demo-bootstrap-token")
    monkeypatch.setenv("DEFAULT_ADMIN_USERNAME", "demo-admin")
    monkeypatch.setenv("DEFAULT_ADMIN_PASSWORD", "demo-pass-123")
    monkeypatch.delenv("SMOKE_ROBOT_CODE", raising=False)
    monkeypatch.setenv("SIM_ROBOT_CODE", "robot-demo-001")
    monkeypatch.setenv("API_BASE_URL", "http://nginx")
    monkeypatch.setenv("ACCEPTANCE_TIMEOUT_SECONDS", "45")

    settings = acceptance_smoke.build_settings()

    assert settings == {
        "api_base": "http://nginx",
        "admin_username": "demo-admin",
        "admin_password": "demo-pass-123",
        "bootstrap_token": "demo-bootstrap-token",
        "robot_code": "robot-demo-001",
        "timeout_seconds": 45,
    }


def test_ensure_robot_reuses_existing_robot():
    calls = []

    class FakeHttp:
        def get(self, url, headers=None, timeout=None):
            calls.append(("GET", url))
            return FakeResponse({"data": {"items": [{"id": "robot-1", "robot_code": "robot-demo-001"}]}})

        def post(self, url, headers=None, json=None, timeout=None):
            calls.append(("POST", url))
            raise AssertionError("existing robot should not trigger registration")

    robot = acceptance_smoke.ensure_robot(
        FakeHttp(),
        "http://nginx",
        {"Authorization": "Bearer token"},
        "robot-demo-001",
    )

    assert robot["id"] == "robot-1"
    assert calls == [("GET", "http://nginx/api/robots")]


def test_ensure_admin_falls_back_to_legacy_demo_passwords():
    attempted_passwords = []

    class FakeHttp:
        def get(self, url, headers=None, timeout=None):
            assert url == "http://nginx/api/system/bootstrap-check"
            return FakeResponse({"data": {"needs_initial_admin": False}})

        def post(self, url, headers=None, json=None, timeout=None):
            assert url == "http://nginx/api/auth/login"
            attempted_passwords.append(json["password"])
            if json["password"] == "super-secret123":
                return FakeResponse({"data": {"token": "legacy-token"}})
            return FakeResponse({"message": "unauthorized"}, status_code=401)

    token = acceptance_smoke.ensure_admin(FakeHttp(), "http://nginx", "admin", "demo-admin-pass-123")

    assert token == "legacy-token"
    assert attempted_passwords == ["demo-admin-pass-123", "super-secret123"]


def test_ensure_admin_uses_bootstrap_token_when_platform_needs_initial_admin():
    class FakeHttp:
        def get(self, url, headers=None, timeout=None):
            assert url == "http://nginx/api/system/bootstrap-check"
            return FakeResponse({"data": {"needs_initial_admin": True}})

        def post(self, url, headers=None, json=None, timeout=None):
            assert url == "http://nginx/api/auth/bootstrap-admin"
            assert headers["X-Bootstrap-Token"] == "bootstrap-secret"
            assert json == {"username": "admin", "password": "demo-admin-pass-123"}
            return FakeResponse({"data": {"token": "bootstrap-token"}})

    token = acceptance_smoke.ensure_admin(
        FakeHttp(),
        "http://nginx",
        "admin",
        "demo-admin-pass-123",
        "bootstrap-secret",
    )

    assert token == "bootstrap-token"


def test_run_smoke_relies_on_simulator_for_asset_uploads():
    recorded_calls = []

    class FakeHttp:
        def get(self, url, headers=None, timeout=None):
            recorded_calls.append(("GET", url, None))
            if url == "http://nginx/api/system/bootstrap-check":
                return FakeResponse({"data": {"needs_initial_admin": False}})
            if url == "http://nginx/api/robots":
                return FakeResponse({"data": {"items": [{"id": "robot-1", "robot_code": "robot-demo-001"}]}})
            if url == "http://nginx/api/tasks/task-1":
                return FakeResponse(
                    {
                        "data": {
                            "id": "task-1",
                            "status": "COMPLETED",
                            "analysis_status": "SUCCESS",
                            "current_message": "分析完成",
                        }
                    }
                )
            if url == "http://nginx/api/assets?task_id=task-1":
                return FakeResponse({"data": {"items": [{"id": "asset-1"}]}})
            if url == "http://nginx/api/results/task-1":
                return FakeResponse({"data": {"id": "result-1", "summary": "ok"}})
            if url == "http://nginx/api/system/alerts":
                return FakeResponse(
                    {
                        "data": {
                            "items": [
                                {
                                    "id": "alert-1",
                                    "is_acknowledged": False,
                                }
                            ]
                        }
                    }
                )
            raise AssertionError(f"unexpected GET {url}")

        def post(self, url, headers=None, json=None, timeout=None):
            recorded_calls.append(("POST", url, json))
            if url == "http://nginx/api/auth/login":
                return FakeResponse({"data": {"token": "token-1"}})
            if url == "http://nginx/api/tasks":
                return FakeResponse({"data": {"id": "task-1"}})
            if url == "http://nginx/api/tasks/task-1/dispatch":
                return FakeResponse({"data": {"status": "DISPATCHED"}})
            raise AssertionError(f"unexpected POST {url}")

        def patch(self, url, headers=None, json=None, timeout=None):
            recorded_calls.append(("PATCH", url, json))
            if url == "http://nginx/api/system/alerts/alert-1/status":
                return FakeResponse({"data": {"id": "alert-1", "is_acknowledged": True}})
            raise AssertionError(f"unexpected PATCH {url}")

        def put(self, url, headers=None, files=None, timeout=None):
            recorded_calls.append(("PUT", url, None))
            raise AssertionError("acceptance smoke must not upload assets directly")

    result = acceptance_smoke.run_smoke(
        http=FakeHttp(),
        settings={
            "api_base": "http://nginx",
            "admin_username": "admin",
            "admin_password": "demo-pass-123",
            "robot_code": "robot-demo-001",
            "timeout_seconds": 30,
        },
    )

    assert result == {
        "task_id": "task-1",
        "status": "COMPLETED",
        "analysis_status": "SUCCESS",
        "asset_count": 1,
        "result_present": True,
        "alerts": 1,
        "acknowledged_alert_id": "alert-1",
    }
    assert ("POST", "http://nginx/api/tasks/task-1/dispatch", None) in recorded_calls
    assert not any("/api/assets/upload-sessions" in url for _, url, _ in recorded_calls)
