import json
import os
import time

import requests
from shared.demo_support import DEFAULT_DEMO_ADMIN_PASSWORD, DEFAULT_DEMO_ADMIN_USERNAME, DEFAULT_SIM_ROBOT_CODE, login_or_bootstrap_admin


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def wait_until(callback, timeout_seconds, message):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        result = callback()
        if result:
            return result
        time.sleep(2)
    raise TimeoutError(message)


def build_settings() -> dict:
    return {
        "api_base": os.getenv("API_BASE_URL", "http://localhost"),
        "admin_username": os.getenv("BOOTSTRAP_ADMIN_USERNAME") or os.getenv("DEFAULT_ADMIN_USERNAME", DEFAULT_DEMO_ADMIN_USERNAME),
        "admin_password": os.getenv("BOOTSTRAP_ADMIN_PASSWORD") or os.getenv("DEFAULT_ADMIN_PASSWORD", DEFAULT_DEMO_ADMIN_PASSWORD),
        "bootstrap_token": os.getenv("BOOTSTRAP_TOKEN", ""),
        "robot_code": os.getenv("SMOKE_ROBOT_CODE") or os.getenv("SIM_ROBOT_CODE", DEFAULT_SIM_ROBOT_CODE),
        "timeout_seconds": int(os.getenv("ACCEPTANCE_TIMEOUT_SECONDS", "90")),
    }


def ensure_admin(http, api_base: str, username: str, password: str, bootstrap_token: str = "") -> str:
    return login_or_bootstrap_admin(http, api_base, username, password, bootstrap_token=bootstrap_token, timeout=10)


def ensure_robot(http, api_base: str, headers: dict, robot_code: str) -> dict:
    robots = http.get(f"{api_base}/api/robots", headers=headers, timeout=10)
    robots.raise_for_status()
    items = robots.json()["data"]["items"]
    existing = next((item for item in items if item["robot_code"] == robot_code), None)
    if existing:
        return existing

    created = http.post(
        f"{api_base}/api/robots/register",
        headers=headers,
        json={
            "robot_code": robot_code,
            "name": "Demo Simulator Robot",
            "protocol": "mqtt",
            "capabilities": {"sensors": ["rgb"]},
            "metadata": {"zone": "demo-lab", "source": "acceptance-smoke"},
        },
        timeout=10,
    )
    created.raise_for_status()
    return created.json()["data"]


def create_task(http, api_base: str, headers: dict, robot: dict) -> dict:
    response = http.post(
        f"{api_base}/api/tasks",
        headers=headers,
        json={
            "name": f"acceptance-smoke-{int(time.time())}",
            "task_type": "phenotyping_capture",
            "robot_id": robot["id"],
            "priority": 3,
            "parameters": {"source": "acceptance-smoke", "mode": "simulator-dispatch"},
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["data"]


def dispatch_task(http, api_base: str, headers: dict, task_id: str) -> None:
    response = http.post(f"{api_base}/api/tasks/{task_id}/dispatch", headers=headers, timeout=10)
    response.raise_for_status()


def wait_for_task_completion(http, api_base: str, headers: dict, task_id: str, timeout_seconds: int) -> dict:
    def task_completed():
        response = http.get(f"{api_base}/api/tasks/{task_id}", headers=headers, timeout=10)
        response.raise_for_status()
        detail = response.json()["data"]
        if detail["status"] == "COMPLETED":
            return detail
        if detail["status"] == "FAILED":
            raise RuntimeError(json.dumps(detail, ensure_ascii=False))
        return None

    return wait_until(task_completed, timeout_seconds, "task did not complete in time")


def acknowledge_latest_unread_alert(http, api_base: str, headers: dict) -> tuple[list[dict], str | None]:
    alerts_response = http.get(f"{api_base}/api/system/alerts", headers=headers, timeout=10)
    alerts_response.raise_for_status()
    alerts = alerts_response.json()["data"]["items"]
    unread = next((item for item in alerts if not item.get("is_acknowledged")), None)
    if not unread:
        return alerts, None

    ack_response = http.patch(
        f"{api_base}/api/system/alerts/{unread['id']}/status",
        headers=headers,
        json={"is_acknowledged": True},
        timeout=10,
    )
    ack_response.raise_for_status()
    return alerts, unread["id"]


def run_smoke(http=None, settings=None) -> dict:
    http = http or requests.Session()
    settings = settings or build_settings()

    token = ensure_admin(
        http,
        settings["api_base"],
        settings["admin_username"],
        settings["admin_password"],
        settings.get("bootstrap_token", ""),
    )
    headers = auth_headers(token)
    robot = ensure_robot(http, settings["api_base"], headers, settings["robot_code"])
    task = create_task(http, settings["api_base"], headers, robot)
    dispatch_task(http, settings["api_base"], headers, task["id"])
    detail = wait_for_task_completion(http, settings["api_base"], headers, task["id"], settings["timeout_seconds"])

    assets_response = http.get(f"{settings['api_base']}/api/assets?task_id={task['id']}", headers=headers, timeout=10)
    assets_response.raise_for_status()
    assets = assets_response.json()["data"]["items"]

    result_response = http.get(f"{settings['api_base']}/api/results/{task['id']}", headers=headers, timeout=10)
    result_response.raise_for_status()
    result = result_response.json()["data"]

    alerts, acknowledged_alert_id = acknowledge_latest_unread_alert(http, settings["api_base"], headers)

    return {
        "task_id": task["id"],
        "status": detail["status"],
        "analysis_status": detail["analysis_status"],
        "asset_count": len(assets),
        "result_present": bool(result),
        "alerts": len(alerts),
        "acknowledged_alert_id": acknowledged_alert_id,
    }


def main():
    summary = run_smoke()
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
