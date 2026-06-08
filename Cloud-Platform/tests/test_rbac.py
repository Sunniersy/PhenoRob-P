"""RBAC permission boundary tests.

Validates that the login_required decorator correctly enforces role-based
access control across admin-only and operator-accessible endpoints.
"""

from datetime import datetime, timedelta, timezone

import jwt
import pytest

from backend.app.config import TestingConfig


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def operator_headers(client, auth_headers):
    """Create an operator user and return its Authorization headers."""
    # Create operator user via admin-only endpoint
    create_resp = client.post(
        "/api/users",
        headers=auth_headers,
        json={"username": "operator1", "password": "operator-pass-123", "role": "operator"},
    )
    assert create_resp.status_code == 201

    # Login as operator
    login_resp = client.post(
        "/api/auth/login",
        json={"username": "operator1", "password": "operator-pass-123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.get_json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def expired_token():
    """Generate an expired JWT access token."""
    payload = {
        "sub": 1,
        "username": "ghost",
        "role": "admin",
        "type": "access",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        "jti": "expired-jti",
    }
    return jwt.encode(payload, TestingConfig.JWT_SECRET, algorithm="HS256")


@pytest.fixture()
def refresh_token_header(client, auth_response_data):
    """Return Authorization header using a refresh token instead of an access token."""
    token = auth_response_data["refresh_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. Admin-only endpoints reject operator
# ---------------------------------------------------------------------------


class TestAdminOnlyEndpointsRejectOperator:
    """operator 访问仅限 admin 的端点应返回 403."""

    def test_operator_rejected_at_register_robot(self, client, operator_headers):
        """POST /api/robots/register requires admin role."""
        resp = client.post(
            "/api/robots/register",
            headers=operator_headers,
            json={
                "robot_code": "r-001",
                "name": "Test Robot",
                "protocol": "mqtt",
                "capabilities": {"sensors": ["rgb"]},
            },
        )
        assert resp.status_code == 403

    def test_operator_rejected_at_list_users(self, client, operator_headers):
        """GET /api/users requires admin role."""
        resp = client.get("/api/users", headers=operator_headers)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 2. Operator can access allowed endpoints
# ---------------------------------------------------------------------------


class TestOperatorCanAccessAllowedEndpoints:
    """operator 可以访问允许的端点（无角色限制或包含 operator 角色限制）."""

    def test_operator_can_list_tasks(self, client, operator_headers):
        """GET /api/tasks has no role restriction -- any authenticated user can access."""
        resp = client.get("/api/tasks", headers=operator_headers)
        assert resp.status_code == 200

    def test_operator_can_view_dashboard_overview(self, client, operator_headers):
        """GET /api/dashboard/overview has no role restriction -- any authenticated user can access."""
        resp = client.get("/api/dashboard/overview", headers=operator_headers)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 3. Unauthenticated request returns 401
# ---------------------------------------------------------------------------


class TestUnauthenticatedRequestReturns401:
    """不带 Authorization header 的请求应返回 401."""

    def test_no_auth_header_returns_401(self, client):
        resp = client.get("/api/tasks")
        assert resp.status_code == 401

    def test_no_auth_header_on_admin_endpoint_returns_401(self, client):
        resp = client.get("/api/users")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 4. Expired token returns 401
# ---------------------------------------------------------------------------


class TestExpiredTokenReturns401:
    """过期的 JWT access token 应返回 401."""

    def test_expired_token_rejected(self, client, expired_token):
        headers = {"Authorization": f"Bearer {expired_token}"}
        resp = client.get("/api/tasks", headers=headers)
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 5. Invalid token returns 401
# ---------------------------------------------------------------------------


class TestInvalidTokenReturns401:
    """格式错误或无效的 token 应返回 401."""

    def test_garbage_token_rejected(self, client):
        headers = {"Authorization": "Bearer not.a.valid.jwt.token"}
        resp = client.get("/api/tasks", headers=headers)
        assert resp.status_code == 401

    def test_empty_bearer_rejected(self, client):
        headers = {"Authorization": "Bearer "}
        resp = client.get("/api/tasks", headers=headers)
        assert resp.status_code == 401

    def test_wrong_scheme_rejected(self, client):
        """Token delivered via Basic scheme instead of Bearer."""
        headers = {"Authorization": "Basic dXNlcjpwYXNz"}
        resp = client.get("/api/tasks", headers=headers)
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 6. Refresh token cannot be used for API authentication
# ---------------------------------------------------------------------------


class TestRefreshTokenCannotBeUsedForAuth:
    """refresh token 不应作为 access token 使用."""

    def test_refresh_token_rejected_as_access_token(self, client, refresh_token_header):
        """A valid refresh token presented as Bearer token should be rejected."""
        resp = client.get("/api/tasks", headers=refresh_token_header)
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 7. Operator cannot manage users
# ---------------------------------------------------------------------------


class TestOperatorCannotManageUsers:
    """operator 不能创建/管理用户."""

    def test_operator_rejected_at_create_user(self, client, operator_headers):
        """POST /api/users requires admin role."""
        resp = client.post(
            "/api/users",
            headers=operator_headers,
            json={"username": "new-user", "password": "new-pass-123", "role": "operator"},
        )
        assert resp.status_code == 403
