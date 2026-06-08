from flask import Blueprint, current_app, request

from backend.app.pagination import parse_pagination_args
from backend.app.rate_limit import rate_limit
from backend.app.validators import validate_password_payload, validate_user_payload
from .utils import api_response, login_required

bp = Blueprint("admin", __name__)


@bp.get("/api/users")
@login_required(["admin"])
def list_users():
    filters = parse_pagination_args(request.args)
    filters["status"] = (request.args.get("status") or "").strip()
    return api_response(current_app.extensions["admin_service"].list_users(filters))


@bp.get("/api/roles")
@login_required(["admin"])
def list_roles():
    filters = parse_pagination_args(request.args)
    return api_response(current_app.extensions["admin_service"].list_roles(filters))


@bp.post("/api/users")
@rate_limit("create_user")
@login_required(["admin"])
def create_user():
    payload = validate_user_payload(request.get_json() or {}, min_length=current_app.config["PASSWORD_MIN_LENGTH"])
    return api_response(current_app.extensions["admin_service"].create_user(payload), status=201)


@bp.patch("/api/users/<user_id>/status")
@login_required(["admin"])
def update_user_status(user_id):
    payload = request.get_json() or {}
    if "is_active" not in payload:
        raise ValueError("is_active is required")
    return api_response(current_app.extensions["admin_service"].update_user_status(user_id, bool(payload.get("is_active"))))


@bp.post("/api/users/<user_id>/reset-password")
@login_required(["admin"])
def reset_password(user_id):
    payload = validate_password_payload(request.get_json() or {}, min_length=current_app.config["PASSWORD_MIN_LENGTH"])
    return api_response(current_app.extensions["admin_service"].reset_password(user_id, payload["password"]))
