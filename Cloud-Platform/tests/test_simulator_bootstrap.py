from importlib import reload


def test_simulator_login_passes_bootstrap_token(monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "http://backend:5000")
    monkeypatch.setenv("DEFAULT_ADMIN_USERNAME", "admin")
    monkeypatch.setenv("DEFAULT_ADMIN_PASSWORD", "demo-admin-pass-123")
    monkeypatch.setenv("BOOTSTRAP_TOKEN", "sim-bootstrap-token")

    import simulator.robot_simulator as robot_simulator

    module = reload(robot_simulator)
    recorded = {}

    def fake_login_or_bootstrap_admin(http, api_base, username, preferred_password, bootstrap_token=None, timeout=10):
        recorded["api_base"] = api_base
        recorded["username"] = username
        recorded["preferred_password"] = preferred_password
        recorded["bootstrap_token"] = bootstrap_token
        recorded["timeout"] = timeout
        return "token-1"

    monkeypatch.setattr(module, "login_or_bootstrap_admin", fake_login_or_bootstrap_admin)

    token = module.login()

    assert token == "token-1"
    assert recorded == {
        "api_base": "http://backend:5000",
        "username": "admin",
        "preferred_password": "demo-admin-pass-123",
        "bootstrap_token": "sim-bootstrap-token",
        "timeout": 10,
    }
