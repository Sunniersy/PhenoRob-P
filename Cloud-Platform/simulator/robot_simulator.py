import hashlib
import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

import requests
from shared.demo_support import DEFAULT_DEMO_ADMIN_PASSWORD, DEFAULT_DEMO_ADMIN_USERNAME, DEFAULT_SIM_ROBOT_CODE, login_or_bootstrap_admin

try:
    import paho.mqtt.client as mqtt
except Exception:  # pragma: no cover
    mqtt = None


API_BASE = os.getenv("API_BASE_URL", "http://backend:5000")
MQTT_HOST = os.getenv("MQTT_BROKER_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
ROBOT_CODE = os.getenv("SIM_ROBOT_CODE", DEFAULT_SIM_ROBOT_CODE)
USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", DEFAULT_DEMO_ADMIN_USERNAME)
PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", DEFAULT_DEMO_ADMIN_PASSWORD)
PROTOCOL_VERSION = os.getenv("MQTT_PROTOCOL_VERSION", "1.0")
BOOTSTRAP_TOKEN = os.getenv("BOOTSTRAP_TOKEN", "")
READY_FILE = Path(os.getenv("SIM_READY_FILE", "/tmp/simulator.ready"))


def log(event: str, **payload):
    print(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "event": event, **payload}, ensure_ascii=False), flush=True)


def mark_ready(ready: bool) -> None:
    if ready:
        READY_FILE.write_text("ready", encoding="utf-8")
        return

    READY_FILE.unlink(missing_ok=True)


def login():
    return login_or_bootstrap_admin(
        requests,
        API_BASE,
        USERNAME,
        PASSWORD,
        bootstrap_token=BOOTSTRAP_TOKEN,
        timeout=10,
    )


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def wait_for_result(token: str, task_id: str, timeout_seconds: int = 60):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        response = requests.get(f"{API_BASE}/api/results/{task_id}", headers=auth_headers(token), timeout=10)
        response.raise_for_status()
        result = response.json()["data"]
        if result:
            log("result.ready", task_id=task_id, result_object_key=result["result_object_key"])
            return result
        time.sleep(2)
    raise TimeoutError(f"timed out waiting for result {task_id}")


def create_upload_session(token: str, task_id: str, file_name: str, asset_type: str = "IMAGE"):
    upload = requests.post(
        f"{API_BASE}/api/assets/upload-sessions",
        headers=auth_headers(token),
        json={"task_id": task_id, "asset_type": asset_type, "file_name": file_name},
        timeout=10,
    )
    upload.raise_for_status()
    return upload.json()["data"]["upload_session_id"]


def complete_upload(token: str, upload_session_id: str, file_name: str, content: str, metadata: dict | None = None, trigger_analysis=True):
    sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    complete = requests.post(
        f"{API_BASE}/api/assets/complete",
        headers=auth_headers(token),
        json={
            "upload_session_id": upload_session_id,
            "file_name": file_name,
            "content": content,
            "metadata": metadata or {},
            "sha256": sha256,
            "trigger_analysis": trigger_analysis,
        },
        timeout=10,
    )
    complete.raise_for_status()
    return sha256


def simulate_svg_capture(task_id: str, index: int) -> str:
    title = escape(f"{ROBOT_CODE} capture {index}")
    subtitle = escape(task_id)
    hue = 118 + index * 7
    accent = 155 + index * 5
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <defs>
    <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0%" stop-color="hsl({hue}, 28%, 18%)" />
      <stop offset="100%" stop-color="hsl({accent}, 35%, 10%)" />
    </linearGradient>
  </defs>
  <rect width="1280" height="720" fill="url(#bg)" />
  <rect x="80" y="68" width="1120" height="584" rx="42" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.16)" />
  <circle cx="340" cy="320" r="120" fill="rgba(166, 217, 91, 0.28)" />
  <circle cx="640" cy="360" r="150" fill="rgba(74, 202, 149, 0.18)" />
  <circle cx="860" cy="270" r="96" fill="rgba(236, 180, 65, 0.18)" />
  <path d="M250 520 C340 410 450 370 520 420 C610 485 730 500 845 438 C936 388 1014 404 1092 500" fill="none" stroke="#91e05d" stroke-width="18" stroke-linecap="round" />
  <path d="M350 520 C410 340 448 220 520 198 C598 174 622 332 680 450" fill="none" stroke="#d7f77b" stroke-width="14" stroke-linecap="round" />
  <text x="120" y="150" fill="#eff7f1" font-size="54" font-family="IBM Plex Sans, PingFang SC, sans-serif">{title}</text>
  <text x="120" y="208" fill="rgba(239,247,241,0.72)" font-size="28" font-family="IBM Plex Sans, PingFang SC, sans-serif">{subtitle}</text>
  <text x="120" y="604" fill="rgba(239,247,241,0.72)" font-size="24" font-family="IBM Plex Sans, PingFang SC, sans-serif">Simulated greenhouse image #{index}</text>
</svg>"""


def handle_dispatch(client, token: str, payload: dict):
    task_id = payload["task_id"]
    if payload.get("protocol_version") != PROTOCOL_VERSION:
        log("dispatch.rejected", reason="protocol_version mismatch", payload=payload)
        return

    log("dispatch.received", task_id=task_id, payload=payload)
    client.publish(
        f"greenhouse/robots/{ROBOT_CODE}/ack",
        json.dumps({"task_id": task_id, "message": "ACK from simulator", "protocol_version": PROTOCOL_VERSION}),
    )
    log("ack.sent", task_id=task_id)
    time.sleep(1)
    client.publish(
        f"greenhouse/robots/{ROBOT_CODE}/progress",
        json.dumps({"task_id": task_id, "progress": 50, "message": "simulator collecting", "protocol_version": PROTOCOL_VERSION}),
    )
    client.publish(
        f"greenhouse/robots/{ROBOT_CODE}/heartbeat",
        json.dumps({"task_id": task_id, "status": "BUSY", "protocol_version": PROTOCOL_VERSION}),
    )
    log("progress.sent", task_id=task_id)
    time.sleep(1)

    upload_session_id = create_upload_session(token, task_id, "simulated-capture.json")
    log("upload.session.created", task_id=task_id, upload_session_id=upload_session_id)

    content = json.dumps({"height": 120.5, "leaf_area": 88.1, "source": "simulator"})
    sha256 = complete_upload(token, upload_session_id, "simulated-capture.json", content, {"source": "simulator"})
    log("upload.completed", task_id=task_id, sha256=sha256)
    wait_for_result(token, task_id)


def handle_command(client, token: str, payload: dict):
    command_id = payload.get("command_id")
    command = payload.get("command")
    if payload.get("protocol_version") != PROTOCOL_VERSION:
        log("command.rejected", reason="protocol_version mismatch", payload=payload)
        return
    client.publish(
        f"greenhouse/robots/{ROBOT_CODE}/command-events",
        json.dumps(
            {
                "command_id": command_id,
                "status": "ACKED",
                "robot_status": "BUSY",
                "protocol_version": PROTOCOL_VERSION,
                "result": {"stage": "accepted"},
            }
        ),
    )
    log("command.acked", command_id=command_id, command=command)
    time.sleep(0.5)

    result = {"stage": "done", "command": command}
    if command == "capture_image":
        task_id = payload.get("params", {}).get("task_id")
        capture_count = max(1, int(payload.get("params", {}).get("count", 1)))
        if task_id:
            for index in range(capture_count):
                file_name = f"capture-{command_id[:8]}-{index + 1}.svg"
                session_id = create_upload_session(token, task_id, file_name)
                complete_upload(
                    token,
                    session_id,
                    file_name,
                    simulate_svg_capture(task_id, index + 1),
                    {"source": "command.capture_image", "command_id": command_id, "index": index + 1},
                    trigger_analysis=index == capture_count - 1,
                )
            result["uploaded_count"] = capture_count
            result["task_id"] = task_id
        else:
            result["uploaded_count"] = 0
    client.publish(
        f"greenhouse/robots/{ROBOT_CODE}/command-events",
        json.dumps(
            {
                "command_id": command_id,
                "status": "COMPLETED",
                "robot_status": "IDLE",
                "protocol_version": PROTOCOL_VERSION,
                "result": result,
            }
        ),
    )
    log("command.completed", command_id=command_id, command=command, result=result)


def on_message(client, userdata, message):
    token = userdata["token"]
    try:
        payload = json.loads(message.payload.decode("utf-8"))
    except (json.JSONDecodeError, TypeError) as exc:
        print(f"[simulator] malformed message on {message.topic}: {exc}")
        return
    if message.topic.endswith("/dispatch"):
        threading.Thread(target=handle_dispatch, args=(client, token, payload), daemon=True).start()
        return
    if message.topic.endswith("/commands"):
        threading.Thread(target=handle_command, args=(client, token, payload), daemon=True).start()
        return
    log("message.ignored", topic=message.topic, payload=payload)


def main():
    if mqtt is None:
        raise RuntimeError("paho-mqtt is required for simulator")
    mark_ready(False)
    try:
        token = login()
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            userdata={"token": token},
        )
        if MQTT_USERNAME:
            client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

        def on_connect(inner_client, userdata, flags, reason_code, properties=None):
            inner_client.subscribe(f"greenhouse/tasks/{ROBOT_CODE}/dispatch")
            inner_client.subscribe(f"greenhouse/robots/{ROBOT_CODE}/commands")
            mark_ready(True)
            log("simulator.ready", api_base=API_BASE, mqtt_host=MQTT_HOST, robot_code=ROBOT_CODE)

        def on_disconnect(inner_client, userdata, *args, **kwargs):
            mark_ready(False)
            log("simulator.disconnected", robot_code=ROBOT_CODE)

        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message
        client.connect(MQTT_HOST, MQTT_PORT)
        client.loop_forever()
    except Exception as exc:  # pragma: no cover
        mark_ready(False)
        log("simulator.error", error=str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
