def test_admin_user_management_and_alerts(client, auth_headers):
    roles = client.get("/api/roles", headers=auth_headers)
    assert roles.status_code == 200
    assert {item["name"] for item in roles.get_json()["data"]["items"]} >= {"admin", "operator"}

    created = client.post(
        "/api/users",
        headers=auth_headers,
        json={"username": "auditor", "password": "secret123", "role": "operator"},
    )
    assert created.status_code == 201
    user = created.get_json()["data"]

    toggled = client.patch(f"/api/users/{user['id']}/status", headers=auth_headers, json={"is_active": False})
    assert toggled.status_code == 200
    assert toggled.get_json()["data"]["is_active"] is False

    bootstrap = client.get("/api/system/bootstrap-check")
    assert bootstrap.status_code == 200
    assert "checks" in bootstrap.get_json()["data"]
    assert "database" in bootstrap.get_json()["data"]["checks"]
    assert bootstrap.get_json()["data"]["needs_initial_admin"] is False

    health = client.get("/api/system/health")
    assert health.status_code == 200
    assert health.get_json()["data"]["mode"] == "liveness"
    assert "checks" not in health.get_json()["data"]

    alerts = client.get("/api/system/alerts", headers=auth_headers)
    assert alerts.status_code == 200
    payload = alerts.get_json()["data"]
    assert payload["page"] == 1
    assert isinstance(payload["items"], list)


def test_register_robot_and_prevent_duplicate_code(client, auth_headers):
    created = client.post(
        "/api/robots/register",
        headers=auth_headers,
        json={
            "robot_code": "robot-qa-01",
            "name": "质检机器人 01",
            "protocol": "mqtt",
            "capabilities": {"sensors": ["rgb"]},
            "metadata": {"zone": "qa-lab"},
        },
    )
    assert created.status_code == 201

    duplicate = client.post(
        "/api/robots/register",
        headers=auth_headers,
        json={
            "robot_code": "robot-qa-01",
            "name": "重复编码机器人",
            "protocol": "mqtt",
            "capabilities": {"sensors": ["rgb"]},
            "metadata": {},
        },
    )
    assert duplicate.status_code == 400
    assert "robot_code already exists" in duplicate.get_json()["message"]
