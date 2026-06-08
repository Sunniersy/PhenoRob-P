from flask import Blueprint, current_app, request

from backend.app.errors import ApiError
from .utils import api_response, current_user_from_request

bp = Blueprint("downloads", __name__, url_prefix="/api/downloads")


@bp.post("/token")
def create_download_token():
    """Exchange a valid JWT for a one-time download token.

    Request body: {"path": "/api/assets/<id>/download"}
    Response: {"dl_token": "<hex-uuid>"}

    The one-time token is valid for 60 seconds and can only be used once,
    bound to the specific resource path. This prevents JWT tokens from
    appearing in server logs, browser history, and proxy logs.
    """
    user = current_user_from_request()
    payload = request.get_json() or {}
    path = payload.get("path", "")

    # Validate the path looks like a legitimate download endpoint
    valid_prefixes = ("/api/assets/", "/api/results/")
    if not any(path.startswith(prefix) for prefix in valid_prefixes):
        raise ApiError("invalid download path", status_code=400)
    if not path.endswith("/download"):
        raise ApiError("invalid download path", status_code=400)

    dl_token = current_app.extensions["download_token_service"].create_token(
        user["id"], path
    )
    return api_response({"dl_token": dl_token})
