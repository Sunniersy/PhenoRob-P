from flask import Blueprint, current_app, request

from backend.app.pagination import parse_pagination_args
from backend.app.validators import validate_command_payload, validate_robot_payload
from .utils import api_response, login_required

bp = Blueprint("robots", __name__, url_prefix="/api/robots")


@bp.post("/register")
@login_required(["admin"])
def register_robot():
    payload = validate_robot_payload(request.get_json() or {})
    return api_response(current_app.extensions["robot_service"].register_robot(payload), status=201)


@bp.get("")
@login_required()
def list_robots():
    # mark_stale_offline is now handled by Celery beat task
    filters = parse_pagination_args(request.args)
    return api_response(current_app.extensions["robot_service"].list_robots(filters))


@bp.get("/<robot_id>")
@login_required()
def get_robot(robot_id):
    # mark_stale_offline is now handled by Celery beat task
    return api_response(current_app.extensions["robot_service"].get_robot(robot_id))


@bp.post("/<robot_id>/commands")
@login_required(["admin", "operator"])
def issue_command(robot_id):
    payload = validate_command_payload(request.get_json() or {})
    operator = request.current_user["username"]
    return api_response(current_app.extensions["robot_service"].issue_command(robot_id, payload, operator=operator), status=201)


@bp.get("/<robot_id>/commands")
@login_required()
def list_commands(robot_id):
    filters = parse_pagination_args(request.args)
    return api_response(current_app.extensions["robot_service"].list_commands(robot_id, filters))
