DEFAULT_DEMO_ADMIN_USERNAME = "admin"
DEFAULT_DEMO_ADMIN_PASSWORD = "demo-admin-pass-123"
DEFAULT_SIM_ROBOT_CODE = "robot-demo-001"
LEGACY_ADMIN_PASSWORDS = ("super-secret123", "admin123")


def _unique(items):
    seen = set()
    ordered = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def admin_password_candidates(preferred_password: str | None) -> list[str]:
    return _unique((preferred_password, DEFAULT_DEMO_ADMIN_PASSWORD, *LEGACY_ADMIN_PASSWORDS))


def login_or_bootstrap_admin(
    http,
    api_base: str,
    username: str,
    preferred_password: str,
    bootstrap_token: str | None = None,
    timeout: int = 10,
) -> str:
    bootstrap = http.get(f"{api_base}/api/system/bootstrap-check", timeout=timeout)
    bootstrap.raise_for_status()
    payload = bootstrap.json()["data"]
    if payload.get("needs_initial_admin"):
        headers = {}
        if bootstrap_token:
            headers["X-Bootstrap-Token"] = bootstrap_token
        response = http.post(
            f"{api_base}/api/auth/bootstrap-admin",
            headers=headers,
            json={"username": username, "password": preferred_password},
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()["data"]["token"]

    for candidate in admin_password_candidates(preferred_password):
        response = http.post(
            f"{api_base}/api/auth/login",
            json={"username": username, "password": candidate},
            timeout=timeout,
        )
        if response.status_code == 401:
            continue
        response.raise_for_status()
        return response.json()["data"]["token"]

    raise RuntimeError("unable to authenticate demo admin with supported default passwords")
