import hashlib


def test_closed_loop_task_flow(app, client, auth_headers, robot):
    create_response = client.post(
        "/api/tasks",
        headers=auth_headers,
        json={
            "name": "番茄植株晨间巡检",
            "task_type": "phenotyping_capture",
            "robot_id": robot["id"],
            "priority": 3,
            "parameters": {"route": "lane-1", "modalities": ["rgb", "depth"]},
        },
    )
    assert create_response.status_code == 201
    task = create_response.get_json()["data"]
    assert task["status"] == "PENDING_DISPATCH"

    dispatch_response = client.post(f"/api/tasks/{task['id']}/dispatch", headers=auth_headers)
    assert dispatch_response.status_code == 200

    transport = app.extensions["transport"]
    transport.emit_ack(robot["robot_code"], {"task_id": task["id"], "message": "ACK", "protocol_version": "1.0"})
    transport.emit_progress(
        robot["robot_code"], {"task_id": task["id"], "progress": 45, "message": "采集中", "protocol_version": "1.0"}
    )
    transport.emit_heartbeat(robot["robot_code"], {"task_id": task["id"], "status": "BUSY", "protocol_version": "1.0"})

    session_response = client.post(
        "/api/assets/upload-sessions",
        headers=auth_headers,
        json={"task_id": task["id"], "asset_type": "IMAGE", "file_name": "capture-001.json"},
    )
    assert session_response.status_code == 201
    upload_session_id = session_response.get_json()["data"]["upload_session_id"]

    complete_response = client.post(
        "/api/assets/complete",
        headers=auth_headers,
        json={
            "upload_session_id": upload_session_id,
            "file_name": "capture-001.json",
            "content": '{"mean_height": 123.4}',
            "sha256": hashlib.sha256(b'{"mean_height": 123.4}').hexdigest(),
            "metadata": {"sensor": "rgb"},
        },
    )
    assert complete_response.status_code == 201

    task_detail_response = client.get(f"/api/tasks/{task['id']}", headers=auth_headers)
    detail = task_detail_response.get_json()["data"]
    assert detail["status"] == "COMPLETED"
    assert detail["result_ready"] is False
    assert detail["analysis_status"] == "DISABLED"
    event_types = [item["event_type"] for item in detail["timeline"]]
    assert "robot_ack" in event_types
    assert "progress" in event_types

    robot_detail_response = client.get(f"/api/robots/{robot['id']}", headers=auth_headers)
    robot_detail = robot_detail_response.get_json()["data"]
    assert robot_detail["last_heartbeat"] is not None
    assert robot_detail["last_heartbeat_payload"]["status"] == "BUSY"

    result_response = client.get(f"/api/results/{task['id']}", headers=auth_headers)
    result = result_response.get_json()["data"]
    assert result is None


def test_dispatch_invalid_state_does_not_mark_failed(client, auth_headers, robot):
    task = client.post(
        "/api/tasks",
        headers=auth_headers,
        json={"name": "重复下发测试", "task_type": "phenotyping_capture", "robot_id": robot["id"], "parameters": {}},
    ).get_json()["data"]

    first = client.post(f"/api/tasks/{task['id']}/dispatch", headers=auth_headers)
    second = client.post(f"/api/tasks/{task['id']}/dispatch", headers=auth_headers)
    assert first.status_code == 200
    assert second.status_code == 400

    detail = client.get(f"/api/tasks/{task['id']}", headers=auth_headers).get_json()["data"]
    assert detail["status"] == "DISPATCHED"


def test_upload_sha_mismatch_returns_400_without_marking_failed(client, auth_headers, robot):
    task = client.post(
        "/api/tasks",
        headers=auth_headers,
        json={"name": "SHA 校验测试", "task_type": "phenotyping_capture", "robot_id": robot["id"], "parameters": {}},
    ).get_json()["data"]
    client.post(f"/api/tasks/{task['id']}/dispatch", headers=auth_headers)
    client.application.extensions["transport"].emit_ack(robot["robot_code"], {"task_id": task["id"], "protocol_version": "1.0"})
    client.application.extensions["transport"].emit_progress(
        robot["robot_code"], {"task_id": task["id"], "progress": 20, "protocol_version": "1.0"}
    )

    upload_session_id = client.post(
        "/api/assets/upload-sessions",
        headers=auth_headers,
        json={"task_id": task["id"], "asset_type": "IMAGE", "file_name": "sha-check.json"},
    ).get_json()["data"]["upload_session_id"]

    response = client.post(
        "/api/assets/complete",
        headers=auth_headers,
        json={
            "upload_session_id": upload_session_id,
            "file_name": "sha-check.json",
            "content": '{"bad": true}',
            "sha256": "deadbeef",
        },
    )
    assert response.status_code == 400

    detail = client.get(f"/api/tasks/{task['id']}", headers=auth_headers).get_json()["data"]
    assert detail["status"] == "DATA_UPLOADING"


def test_duplicate_upload_complete_is_idempotent(client, auth_headers, robot):
    task = client.post(
        "/api/tasks",
        headers=auth_headers,
        json={"name": "幂等上传测试", "task_type": "phenotyping_capture", "robot_id": robot["id"], "parameters": {}},
    ).get_json()["data"]
    client.post(f"/api/tasks/{task['id']}/dispatch", headers=auth_headers)
    client.application.extensions["transport"].emit_ack(robot["robot_code"], {"task_id": task["id"], "protocol_version": "1.0"})
    client.application.extensions["transport"].emit_progress(
        robot["robot_code"], {"task_id": task["id"], "progress": 20, "protocol_version": "1.0"}
    )

    session = client.post(
        "/api/assets/upload-sessions",
        headers=auth_headers,
        json={"task_id": task["id"], "asset_type": "IMAGE", "file_name": "idempotent.json"},
    ).get_json()["data"]["upload_session_id"]
    content = '{"ok": true}'
    sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()

    first = client.post(
        "/api/assets/complete",
        headers=auth_headers,
        json={"upload_session_id": session, "file_name": "idempotent.json", "content": content, "sha256": sha256},
    )
    second = client.post(
        "/api/assets/complete",
        headers=auth_headers,
        json={"upload_session_id": session, "file_name": "idempotent.json", "content": content, "sha256": sha256},
    )
    assert first.status_code == 201
    assert second.status_code == 200
    assert second.get_json()["data"]["idempotent"] is True


def test_robot_command_roundtrip_and_asset_gallery_download(client, auth_headers, robot):
    task = client.post(
        "/api/tasks",
        headers=auth_headers,
        json={"name": "图库验证任务", "task_type": "phenotyping_capture", "robot_id": robot["id"], "parameters": {}},
    ).get_json()["data"]
    client.post(f"/api/tasks/{task['id']}/dispatch", headers=auth_headers)

    command = client.post(
        f"/api/robots/{robot['id']}/commands",
        headers=auth_headers,
        json={"command": "capture_image", "params": {"task_id": task["id"], "count": 2}},
    )
    assert command.status_code == 201
    command_id = command.get_json()["data"]["id"]

    transport = client.application.extensions["transport"]
    transport.emit_command_event(
        robot["robot_code"],
        {
            "command_id": command_id,
            "status": "ACKED",
            "protocol_version": "1.0",
            "result": {"stage": "accepted"},
        },
    )
    transport.emit_command_event(
        robot["robot_code"],
        {
            "command_id": command_id,
            "status": "COMPLETED",
            "protocol_version": "1.0",
            "result": {"uploaded_count": 2},
        },
    )

    commands = client.get(f"/api/robots/{robot['id']}/commands", headers=auth_headers)
    assert commands.status_code == 200
    assert commands.get_json()["data"]["items"][0]["status"] == "COMPLETED"

    session_ids = []
    payloads = ['<svg xmlns="http://www.w3.org/2000/svg"></svg>', '<svg xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10"/></svg>']
    for index in range(2):
        session = client.post(
            "/api/assets/upload-sessions",
            headers=auth_headers,
            json={"task_id": task["id"], "asset_type": "IMAGE", "file_name": f"capture-{index + 1}.svg"},
        )
        assert session.status_code == 201
        session_ids.append(session.get_json()["data"]["upload_session_id"])

    for index, session_id in enumerate(session_ids):
        response = client.post(
            "/api/assets/complete",
            headers=auth_headers,
            json={
                "upload_session_id": session_id,
                "file_name": f"capture-{index + 1}.svg",
                "content": payloads[index],
                "sha256": hashlib.sha256(payloads[index].encode("utf-8")).hexdigest(),
                "trigger_analysis": index == len(session_ids) - 1,
            },
        )
        assert response.status_code == 201

    asset_list = client.get(f"/api/assets?task_id={task['id']}", headers=auth_headers)
    assert asset_list.status_code == 200
    assets = asset_list.get_json()["data"]["items"]
    assert len(assets) == 2
    assert all(item["task_id"] == task["id"] for item in assets)

    asset_detail = client.get(f"/api/assets/{assets[0]['id']}", headers=auth_headers)
    assert asset_detail.status_code == 200
    assert asset_detail.get_json()["data"]["result"] is None

    # Old query-string JWT token approach should no longer work
    download_legacy = client.get(f"/api/assets/{assets[0]['id']}/download?token=test", headers=auth_headers)
    assert download_legacy.status_code == 401

    # Exchange JWT for a one-time download token
    dl_token_resp = client.post(
        "/api/downloads/token",
        headers=auth_headers,
        json={"path": f"/api/assets/{assets[0]['id']}/download"},
    )
    assert dl_token_resp.status_code == 200
    dl_token = dl_token_resp.get_json()["data"]["dl_token"]

    # Use the one-time token to download
    download = client.get(f"/api/assets/{assets[0]['id']}/download?dl_token={dl_token}")
    assert download.status_code == 200
    assert download.mimetype == "image/svg+xml"

    # One-time token should be consumed (re-use fails)
    download_reuse = client.get(f"/api/assets/{assets[0]['id']}/download?dl_token={dl_token}")
    assert download_reuse.status_code == 401


def test_demo_analysis_provider_generates_result():
    from backend.app import create_app
    from backend.app.config import TestingConfig

    class DemoAnalysisConfig(TestingConfig):
        ANALYSIS_PROVIDER = "demo"
        ANALYSIS_LATENCY_SECONDS = 0
        LOCAL_STORAGE_PATH = "storage/test/demo-analysis"

    app = create_app(DemoAnalysisConfig)
    client = app.test_client()

    bootstrap = client.post("/api/auth/bootstrap-admin", json={"username": "admin", "password": "super-secret123"})
    token = bootstrap.get_json()["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}

    robot = client.post(
        "/api/robots/register",
        headers=headers,
        json={
            "robot_code": "robot-demo-001",
            "name": "Demo Robot",
            "protocol": "mqtt",
            "capabilities": {"sensors": ["rgb"]},
            "metadata": {"zone": "demo-lab"},
        },
    ).get_json()["data"]

    task = client.post(
        "/api/tasks",
        headers=headers,
        json={"name": "demo-analysis-task", "task_type": "manual_image_import", "robot_id": robot["id"], "parameters": {}},
    ).get_json()["data"]
    client.post(f"/api/tasks/{task['id']}/dispatch", headers=headers)
    app.extensions["transport"].emit_ack(robot["robot_code"], {"task_id": task["id"], "protocol_version": "1.0"})
    app.extensions["transport"].emit_progress(robot["robot_code"], {"task_id": task["id"], "progress": 100, "protocol_version": "1.0"})

    upload_session_id = client.post(
        "/api/assets/upload-sessions",
        headers=headers,
        json={"task_id": task["id"], "asset_type": "IMAGE", "file_name": "demo.svg"},
    ).get_json()["data"]["upload_session_id"]

    content = '<svg xmlns="http://www.w3.org/2000/svg"><rect width="20" height="10"/></svg>'
    complete = client.post(
        "/api/assets/complete",
        headers=headers,
        json={
            "upload_session_id": upload_session_id,
            "file_name": "demo.svg",
            "content": content,
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "metadata": {"source": "demo-test"},
        },
    )

    assert complete.status_code == 201

    detail = client.get(f"/api/tasks/{task['id']}", headers=headers).get_json()["data"]
    assert detail["status"] == "COMPLETED"
    assert detail["result_ready"] is True
    assert detail["analysis_status"] == "SUCCESS"
    assert detail["result"]["summary"]
    assert detail["result"]["result_json"]["provider"] == "demo"


def test_robot_command_dispatch_failure_persists_failed_command_record(client, auth_headers, robot, monkeypatch):
    transport = client.application.extensions["transport"]

    def fail_publish_command(robot_code, payload):
        raise RuntimeError("broker unavailable")

    monkeypatch.setattr(transport, "publish_command", fail_publish_command)

    response = client.post(
        f"/api/robots/{robot['id']}/commands",
        headers=auth_headers,
        json={"command": "return_home", "params": {}},
    )

    assert response.status_code == 502
    assert response.get_json()["message"] == "robot command dispatch failed"

    commands = client.get(f"/api/robots/{robot['id']}/commands", headers=auth_headers)
    assert commands.status_code == 200
    items = commands.get_json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["command"] == "return_home"
    assert items[0]["status"] == "FAILED"
    assert items[0]["error_message"] == "broker unavailable"


def test_task_dispatch_failure_marks_task_failed_and_returns_upstream_error(client, auth_headers, robot, monkeypatch):
    transport = client.application.extensions["transport"]
    task = client.post(
        "/api/tasks",
        headers=auth_headers,
        json={"name": "dispatch-failure", "task_type": "phenotyping_capture", "robot_id": robot["id"], "parameters": {}},
    ).get_json()["data"]

    def fail_publish_task(robot_code, payload):
        raise RuntimeError("mqtt broker unavailable")

    monkeypatch.setattr(transport, "publish_task", fail_publish_task)

    response = client.post(f"/api/tasks/{task['id']}/dispatch", headers=auth_headers)

    assert response.status_code == 502
    assert response.get_json()["message"] == "task dispatch failed"

    detail = client.get(f"/api/tasks/{task['id']}", headers=auth_headers).get_json()["data"]
    assert detail["status"] == "FAILED"
    assert detail["current_message"] == "任务下发失败"
    assert detail["failure_reason"] == "mqtt broker unavailable"
