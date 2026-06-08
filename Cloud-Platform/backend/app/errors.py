class ApiError(Exception):
    def __init__(self, message: str, status_code: int = 400, errors: dict | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors or {}


class ValidationError(ApiError):
    def __init__(self, errors: dict[str, str], message: str = "validation error"):
        super().__init__(message=message, status_code=400, errors=errors)


class NotFoundError(ApiError):
    def __init__(self, resource: str = "resource", errors: dict | None = None):
        super().__init__(message=f"{resource} not found", status_code=404, errors=errors)


class ConflictError(ApiError):
    def __init__(self, message: str, errors: dict | None = None):
        super().__init__(message=message, status_code=409, errors=errors)


class AuthenticationError(ApiError):
    def __init__(self, message: str = "unauthorized", errors: dict | None = None):
        super().__init__(message=message, status_code=401, errors=errors)


class AuthorizationError(ApiError):
    def __init__(self, message: str = "forbidden", errors: dict | None = None):
        super().__init__(message=message, status_code=403, errors=errors)


class UpstreamError(ApiError):
    def __init__(self, message: str, errors: dict | None = None):
        super().__init__(message=message, status_code=502, errors=errors)
