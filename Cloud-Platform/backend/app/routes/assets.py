from io import BytesIO

from flask import Blueprint, Response, current_app, request, send_file, stream_with_context

from backend.app.errors import ApiError
from backend.app.pagination import parse_pagination_args
from backend.app.validators import (
    validate_legacy_upload_complete_payload,
    validate_upload_file_name,
    validate_upload_finalize_payload,
    validate_upload_session_payload,
)
from .utils import api_response, current_user_from_download_token, login_required

bp = Blueprint("assets", __name__, url_prefix="/api/assets")


def _enforce_upload_size(content: bytes) -> None:
    if len(content) > int(current_app.config["MAX_UPLOAD_SIZE_BYTES"]):
        raise ApiError("upload payload too large", status_code=413)


@bp.post("/upload-sessions")
@login_required(["admin", "operator"])
def create_upload_session():
    payload = validate_upload_session_payload(request.get_json() or {})
    return api_response(current_app.extensions["asset_service"].create_upload_session(payload), status=201)


@bp.post("/complete")
@login_required(["admin", "operator"])
def complete_upload():
    payload = validate_legacy_upload_complete_payload(request.get_json() or {})
    _enforce_upload_size(payload["content"].encode("utf-8"))
    data = current_app.extensions["asset_service"].complete_upload(payload)
    return api_response(data, status=200 if data.get("idempotent") else 201)


@bp.put("/upload-sessions/<upload_session_id>/content")
@login_required(["admin", "operator"])
def upload_session_content(upload_session_id):
    file = request.files.get("file")
    if not file:
        raise ValueError("file is required")
    file_name = validate_upload_file_name(file.filename)
    content = file.read()
    _enforce_upload_size(content)
    data = current_app.extensions["asset_service"].upload_session_content(upload_session_id, file_name, content)
    return api_response(data)


@bp.post("/upload-sessions/<upload_session_id>/complete")
@login_required(["admin", "operator"])
def complete_staged_upload(upload_session_id):
    payload = validate_upload_finalize_payload(request.get_json() or {})
    data = current_app.extensions["asset_service"].complete_uploaded_session(upload_session_id, **payload)
    return api_response(data, status=200 if data.get("idempotent") else 201)


@bp.get("")
@login_required()
def list_assets():
    filters = {
        **parse_pagination_args(request.args),
        "task_id": request.args.get("task_id"),
        "robot_id": request.args.get("robot_id"),
        "asset_type": request.args.get("asset_type"),
        "date_from": request.args.get("date_from"),
        "date_to": request.args.get("date_to"),
    }
    return api_response(current_app.extensions["asset_service"].list_assets(filters))


@bp.get("/<asset_id>")
@login_required()
def get_asset(asset_id):
    return api_response(current_app.extensions["asset_service"].get_asset(asset_id))


@bp.get("/<asset_id>/download")
def download_asset(asset_id):
    resource_path = f"/api/assets/{asset_id}/download"
    current_user_from_download_token(resource_path)

    # Get asset metadata first
    asset_service = current_app.extensions["asset_service"]
    asset = asset_service.get_asset(asset_id)

    # For large files, use streaming
    content_type = asset.get("content_type", "application/octet-stream")
    file_name = asset.get("file_name", "download")
    size_bytes = asset.get("size_bytes", 0)

    # If file is small enough (< 10MB), use traditional download
    if size_bytes < 10 * 1024 * 1024:
        data = asset_service.download_asset(asset_id)
        return send_file(
            BytesIO(data["content"]),
            mimetype=data["content_type"],
            as_attachment=request.args.get("download") == "1",
            download_name=data["asset"]["file_name"],
        )

    # For large files, use streaming response
    def generate():
        # Get the storage backend
        storage = current_app.extensions["storage"]
        object_key = asset.get("object_key")

        # Stream the file in chunks
        chunk_size = 8192  # 8KB chunks
        with storage.open_stream(object_key) as stream:
            while True:
                chunk = stream.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    response = Response(
        stream_with_context(generate()),
        mimetype=content_type,
        headers={
            "Content-Disposition": f'{"attachment" if request.args.get("download") == "1" else "inline"}; filename="{file_name}"',
            "Content-Length": str(size_bytes) if size_bytes else None,
        }
    )

    return response
