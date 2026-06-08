from functools import wraps

from flask import current_app, g, jsonify, request
from jwt import InvalidTokenError

from backend.app.errors import AuthenticationError


def api_response(data=None, message="ok", status=200, errors=None):
    payload = {
        "message": message,
        "data": data,
        "errors": errors or {},
        "request_id": getattr(g, "request_id", ""),
    }
    return jsonify(payload), status


def _current_user():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise AuthenticationError("missing bearer token")
    token = auth_header.split(" ", 1)[1]
    return _load_current_user(token)


def current_user_from_request():
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    if not token:
        raise AuthenticationError("missing bearer token")
    return _load_current_user(token)


def current_user_from_download_token(resource_path: str):
    """Authenticate a request using a one-time download token.

    Validates the dl_token query parameter against the download token service,
    ensuring the token matches the expected resource path. Returns the
    authenticated user dict.
    """
    dl_token = request.args.get("dl_token")
    if not dl_token:
        raise AuthenticationError("missing download token")
    user_id = current_app.extensions["download_token_service"].consume_token(
        dl_token, resource_path
    )
    if user_id is None:
        raise AuthenticationError("invalid or expired download token")
    try:
        return current_app.extensions["auth_service"].get_user_by_id(user_id)
    except ValueError as exc:
        raise AuthenticationError(str(exc)) from exc


def _load_current_user(token: str):
    try:
        return current_app.extensions["auth_service"].current_user(token)
    except InvalidTokenError as exc:
        raise AuthenticationError("invalid token") from exc
    except ValueError as exc:
        raise AuthenticationError(str(exc)) from exc


def login_required(roles=None):
    roles = roles or []

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                user = current_user_from_request()
            except AuthenticationError as exc:
                return api_response(None, str(exc), 401)
            if roles and user["role"] not in roles:
                return api_response(None, "forbidden", 403)
            request.current_user = user
            return func(*args, **kwargs)

        return wrapper

    return decorator
