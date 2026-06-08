from flask import Blueprint, current_app
from flask import request

from backend.app.pagination import parse_pagination_args
from .utils import api_response, login_required

bp = Blueprint("system", __name__, url_prefix="/api/system")


@bp.get("/health")
def health():
    return api_response(current_app.extensions["system_service"].health())


@bp.get("/bootstrap-check")
def bootstrap_check():
    return api_response(current_app.extensions["system_service"].bootstrap_check())


@bp.get("/alerts")
@login_required(["admin"])
def alerts():
    filters = parse_pagination_args(request.args)
    filters["status"] = (request.args.get("status") or "").strip()
    return api_response(current_app.extensions["system_service"].list_alerts(filters))


@bp.get("/runtime")
@login_required()
def runtime():
    return api_response(current_app.extensions["system_service"].runtime())


@bp.get("/release-readiness")
@login_required(["admin"])
def release_readiness():
    return api_response(current_app.extensions["system_service"].release_readiness())


@bp.patch("/alerts/<alert_id>/status")
@login_required(["admin"])
def update_alert_status(alert_id):
    payload = request.get_json() or {}
    if "is_acknowledged" not in payload:
        raise ValueError("is_acknowledged is required")
    return api_response(
        current_app.extensions["system_service"].acknowledge_alert(
            alert_id, request.current_user["username"], bool(payload["is_acknowledged"])
        )
    )
