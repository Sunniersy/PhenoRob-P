from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from backend.app.models import Role, User


def test_bootstrap_admin_login_and_me(client, bootstrap_admin_payload):
    bootstrap_response = client.post("/api/auth/bootstrap-admin", json=bootstrap_admin_payload)
    assert bootstrap_response.status_code == 201
    token = bootstrap_response.get_json()["data"]["token"]

    login_response = client.post("/api/auth/login", json=bootstrap_admin_payload)
    assert login_response.status_code == 200
    assert login_response.get_json()["data"]["user"]["username"] == bootstrap_admin_payload["username"]

    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.get_json()["data"]["username"] == bootstrap_admin_payload["username"]
    assert me_response.get_json()["data"]["role"] == "admin"


def test_bootstrap_admin_can_only_run_once(client, bootstrap_admin_payload):
    first = client.post("/api/auth/bootstrap-admin", json=bootstrap_admin_payload)
    second = client.post("/api/auth/bootstrap-admin", json={"username": "admin-2", "password": "another-secret123"})

    assert first.status_code == 201
    assert second.status_code == 409


def test_inactive_user_cannot_login(client, auth_headers):
    created = client.post(
        "/api/users",
        headers=auth_headers,
        json={"username": "inactive-user", "password": "secret123", "role": "operator"},
    )
    user_id = created.get_json()["data"]["id"]
    client.patch(f"/api/users/{user_id}/status", headers=auth_headers, json={"is_active": False})

    login_response = client.post("/api/auth/login", json={"username": "inactive-user", "password": "secret123"})
    assert login_response.status_code == 401


def test_ensure_roles_tolerates_concurrent_insert(app, monkeypatch):
    auth_service = app.extensions["auth_service"]
    db = app.extensions["db"]
    original_session_factory = db.session

    cleanup_session = original_session_factory()
    try:
        cleanup_session.query(Role).delete()
        cleanup_session.commit()
    finally:
        cleanup_session.close()

    session = original_session_factory()
    original_flush = session.flush
    state = {"raised": False}

    def flaky_flush(*args, **kwargs):
        pending_role_names = {item.name for item in session.new if isinstance(item, Role)}
        if pending_role_names and not state["raised"]:
            state["raised"] = True
            concurrent_session = original_session_factory()
            try:
                concurrent_session.add_all([Role(name="admin"), Role(name="operator")])
                concurrent_session.commit()
            finally:
                concurrent_session.close()
            raise IntegrityError("INSERT INTO roles", {}, Exception("duplicate role"))
        return original_flush(*args, **kwargs)

    monkeypatch.setattr(session, "flush", flaky_flush)
    monkeypatch.setattr(db, "session", lambda: session)

    auth_service.ensure_roles()

    verification_session = original_session_factory()
    try:
        roles = sorted(role.name for role in verification_session.query(Role).all())
    finally:
        verification_session.close()

    assert roles == ["admin", "operator"]


def test_sync_demo_admin_resets_existing_admin_password_and_reactivates_user(app, client):
    auth_service = app.extensions["auth_service"]

    bootstrap = client.post("/api/auth/bootstrap-admin", json={"username": "admin", "password": "legacy-secret123"})
    assert bootstrap.status_code == 201

    session = app.extensions["db"].session()
    try:
        user = session.scalar(select(User).where(User.username == "admin"))
        user.is_active = False
        session.commit()
    finally:
        session.close()

    payload = auth_service.sync_demo_admin("admin", "demo-admin-pass-123")

    assert payload["user"]["username"] == "admin"
    assert payload["user"]["is_active"] is True
    assert payload["user"]["role"] == "admin"
    assert payload["user"]["must_change_password"] is False

    old_login = client.post("/api/auth/login", json={"username": "admin", "password": "legacy-secret123"})
    assert old_login.status_code == 401

    new_login = client.post("/api/auth/login", json={"username": "admin", "password": "demo-admin-pass-123"})
    assert new_login.status_code == 200


# --- Refresh Token Tests ---


def test_login_returns_refresh_token(client, bootstrap_admin_payload):
    client.post("/api/auth/bootstrap-admin", json=bootstrap_admin_payload)
    login_response = client.post("/api/auth/login", json=bootstrap_admin_payload)
    data = login_response.get_json()["data"]
    assert "token" in data
    assert "refresh_token" in data
    assert data["token"] != data["refresh_token"]


def test_bootstrap_returns_refresh_token(client, bootstrap_admin_payload):
    response = client.post("/api/auth/bootstrap-admin", json=bootstrap_admin_payload)
    data = response.get_json()["data"]
    assert "token" in data
    assert "refresh_token" in data


def test_refresh_endpoint_returns_new_tokens(client, bootstrap_admin_payload):
    client.post("/api/auth/bootstrap-admin", json=bootstrap_admin_payload)
    login_response = client.post("/api/auth/login", json=bootstrap_admin_payload)
    data = login_response.get_json()["data"]
    old_access = data["token"]
    old_refresh = data["refresh_token"]

    refresh_response = client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert refresh_response.status_code == 200
    new_data = refresh_response.get_json()["data"]
    assert "token" in new_data
    assert "refresh_token" in new_data
    # New tokens should differ from old ones (rotation)
    assert new_data["token"] != old_access
    assert new_data["refresh_token"] != old_refresh


def test_refresh_with_invalid_token_returns_401(client):
    response = client.post("/api/auth/refresh", json={"refresh_token": "invalid-token"})
    assert response.status_code == 401


def test_refresh_with_missing_token_returns_400(client):
    response = client.post("/api/auth/refresh", json={})
    assert response.status_code == 400


def test_refresh_with_old_revoked_token_returns_401(client, bootstrap_admin_payload):
    """After refreshing, the old refresh token should be revoked (rotation)."""
    client.post("/api/auth/bootstrap-admin", json=bootstrap_admin_payload)
    login_response = client.post("/api/auth/login", json=bootstrap_admin_payload)
    old_refresh = login_response.get_json()["data"]["refresh_token"]

    # First refresh succeeds
    client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    # Second refresh with the same old token should fail
    response = client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
    assert response.status_code == 401


def test_access_token_with_type_claim_works_with_me(client, bootstrap_admin_payload):
    """The new access tokens (with type=access claim) should work with /auth/me."""
    client.post("/api/auth/bootstrap-admin", json=bootstrap_admin_payload)
    login_response = client.post("/api/auth/login", json=bootstrap_admin_payload)
    token = login_response.get_json()["data"]["token"]

    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.get_json()["data"]["role"] == "admin"


def test_refresh_token_cannot_be_used_as_access_token(client, bootstrap_admin_payload):
    """A refresh token should not be accepted as an access token via Bearer auth."""
    client.post("/api/auth/bootstrap-admin", json=bootstrap_admin_payload)
    login_response = client.post("/api/auth/login", json=bootstrap_admin_payload)
    refresh_token = login_response.get_json()["data"]["refresh_token"]

    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {refresh_token}"})
    assert me_response.status_code == 401


def test_logout_revokes_refresh_token(client, bootstrap_admin_payload):
    client.post("/api/auth/bootstrap-admin", json=bootstrap_admin_payload)
    login_response = client.post("/api/auth/login", json=bootstrap_admin_payload)
    refresh_token = login_response.get_json()["data"]["refresh_token"]

    logout_response = client.post("/api/auth/logout", json={"refresh_token": refresh_token})
    assert logout_response.status_code == 200

    # The revoked refresh token should no longer work
    refresh_response = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_response.status_code == 401


def test_logout_without_token_succeeds(client):
    response = client.post("/api/auth/logout", json={})
    assert response.status_code == 200
