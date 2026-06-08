from flask import Blueprint, current_app
from io import BytesIO
from flask import send_file, request

from backend.app.pagination import parse_pagination_args

from .utils import api_response, current_user_from_download_token, login_required

bp = Blueprint("results", __name__, url_prefix="/api/results")


@bp.get("")
@login_required()
def list_results():
    filters = parse_pagination_args(request.args)
    return api_response(current_app.extensions["result_service"].list_results(filters))


@bp.get("/<task_id>")
@login_required()
def get_result(task_id):
    return api_response(current_app.extensions["result_service"].get_result_by_task(task_id))


@bp.get("/<task_id>/download")
def download_result(task_id):
    resource_path = f"/api/results/{task_id}/download"
    current_user_from_download_token(resource_path)
    result = current_app.extensions["result_service"].get_result_by_task(task_id)
    if not result or not result.get("result_object_key"):
        raise ValueError("result file not found")
    content = current_app.extensions["storage"].get_bytes(result["result_object_key"])
    return send_file(
        BytesIO(content),
        mimetype="application/json",
        as_attachment=request.args.get("download") == "1",
        download_name=f"{task_id}-analysis.json",
    )
