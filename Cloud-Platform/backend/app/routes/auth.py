from flask import Blueprint, current_app, request

from backend.app.rate_limit import rate_limit, rate_limit_login
from backend.app.validators import validate_bootstrap_admin_payload
from .utils import api_response, login_required

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/login")
@rate_limit_login
def login():
    payload = request.get_json() or {}
    result = current_app.extensions["auth_service"].login(payload.get("username", ""), payload.get("password", ""))
    if not result:
        return api_response(None, "invalid credentials", 401)
    return api_response(result)


@bp.post("/refresh")
@rate_limit("refresh")
def refresh():
    payload = request.get_json() or {}
    refresh_token = payload.get("refresh_token", "")
    if not refresh_token:
        return api_response(None, "refresh_token is required", 400)
    result = current_app.extensions["auth_service"].refresh_access_token(refresh_token)
    if not result:
        return api_response(None, "invalid or expired refresh token", 401)
    return api_response(result)


@bp.post("/logout")
def logout():
    payload = request.get_json() or {}
    refresh_token = payload.get("refresh_token", "")
    current_app.extensions["auth_service"].logout(refresh_token)
    return api_response(None, "logged out")


@bp.post("/bootstrap-admin")
@rate_limit_login
def bootstrap_admin():
    expected_token = current_app.config.get("BOOTSTRAP_TOKEN", "")
    if expected_token and request.headers.get("X-Bootstrap-Token", "") != expected_token:
        return api_response(None, "invalid bootstrap token", 401)
    payload = validate_bootstrap_admin_payload(
        request.get_json() or {},
        min_length=current_app.config["PASSWORD_MIN_LENGTH"],
    )
    return api_response(
        current_app.extensions["auth_service"].bootstrap_admin(payload["username"], payload["password"]),
        status=201,
    )


@bp.get("/me")
@login_required()
def me():
    return api_response(request.current_user)
