from flask import Blueprint, current_app, request

from backend.app.pagination import parse_pagination_args
from backend.app.validators import validate_task_payload
from .utils import api_response, login_required

bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")


@bp.post("")
@login_required(["admin", "operator"])
def create_task():
    payload = validate_task_payload(request.get_json() or {})
    data = current_app.extensions["task_service"].create_task(payload, user_id=request.current_user["id"])
    return api_response(data, status=201)


@bp.get("")
@login_required()
def list_tasks():
    filters = parse_pagination_args(request.args)
    return api_response(current_app.extensions["task_service"].list_tasks(filters))


@bp.get("/<task_id>")
@login_required()
def get_task(task_id):
    return api_response(current_app.extensions["task_service"].get_task(task_id))


@bp.post("/<task_id>/dispatch")
@login_required(["admin", "operator"])
def dispatch_task(task_id):
    return api_response(current_app.extensions["task_service"].dispatch_task(task_id))


@bp.post("/<task_id>/retry")
@login_required(["admin", "operator"])
def retry_task(task_id):
    return api_response(current_app.extensions["task_service"].retry_task(task_id))


@bp.post("/<task_id>/cancel")
@login_required(["admin", "operator"])
def cancel_task(task_id):
    return api_response(current_app.extensions["task_service"].cancel_task(task_id, request.current_user["username"]))
