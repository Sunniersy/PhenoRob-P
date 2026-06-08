import shutil
from pathlib import Path

import pytest

from backend.app import create_app
from backend.app.config import TestingConfig


@pytest.fixture()
def app():
    storage_dir = Path("storage/test")
    if storage_dir.exists():
        shutil.rmtree(storage_dir)
    application = create_app(TestingConfig)
    yield application
    if storage_dir.exists():
        shutil.rmtree(storage_dir)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def bootstrap_admin_payload():
    return {"username": "admin", "password": "super-secret123"}


@pytest.fixture()
def auth_headers(client, bootstrap_admin_payload):
    response = client.post("/api/auth/bootstrap-admin", json=bootstrap_admin_payload)
    token = response.get_json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def auth_response_data(client, bootstrap_admin_payload):
    """Returns the full auth response data including refresh_token."""
    response = client.post("/api/auth/bootstrap-admin", json=bootstrap_admin_payload)
    return response.get_json()["data"]


@pytest.fixture()
def robot(client, auth_headers):
    response = client.post(
        "/api/robots/register",
        headers=auth_headers,
        json={
            "robot_code": "robot-001",
            "name": "温室表型机器人 001",
            "protocol": "mqtt",
            "capabilities": {"sensors": ["rgb", "depth", "point_cloud"]},
            "metadata": {"zone": "greenhouse-a"},
        },
    )
    return response.get_json()["data"]
