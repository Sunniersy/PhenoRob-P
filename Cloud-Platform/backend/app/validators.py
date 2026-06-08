from backend.app.errors import ValidationError


def _validate_password_complexity(password: str, field: str = "password") -> None:
    """验证密码复杂度：至少包含大写字母、小写字母、数字中的两种。"""
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)

    categories = sum([has_upper, has_lower, has_digit])
    if categories < 2:
        raise ValidationError({field: "密码必须包含大写字母、小写字母、数字中的至少两种"})


def _validate_string_length(value: str, field: str, max_length: int = 255) -> str:
    """验证字符串长度不超过指定限制。"""
    if len(value) > max_length:
        raise ValidationError({field: f"长度不能超过 {max_length} 个字符"})
    return value


def escape_like_wildcards(value: str) -> str:
    """Escape SQL LIKE wildcard characters in user input.

    Escapes ``%``, ``_`` and ``\\`` so that they are treated as literal
    characters rather than wildcards when used in an ILIKE / LIKE clause.
    """
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _ensure_non_empty_string(value, message: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        raise ValueError(message)
    return cleaned


def _validate_path_segment(value: str, field: str, message: str) -> None:
    if "\x00" in value or "/" in value or "\\" in value or value in {".", ".."}:
        raise ValidationError({field: message})


def validate_upload_file_name(file_name: str) -> str:
    cleaned = str(file_name or "").strip()
    if not cleaned:
        raise ValidationError({"file_name": "文件名不能为空"})
    _validate_string_length(cleaned, "file_name", max_length=255)
    _validate_path_segment(cleaned, "file_name", "文件名不能包含路径分隔符")
    return cleaned


def validate_task_payload(payload: dict) -> dict:
    errors = {}
    name = str(payload.get("name") or "").strip()
    task_type = str(payload.get("task_type") or "").strip()
    robot_id = str(payload.get("robot_id") or "").strip()

    if not name:
        errors["name"] = "任务名称不能为空"
    elif len(name) > 200:
        errors["name"] = "长度不能超过 200 个字符"
    if not task_type:
        errors["task_type"] = "任务类型不能为空"
    if not robot_id:
        errors["robot_id"] = "目标机器人不能为空"

    parameters = payload.get("parameters", {})
    if parameters is None:
        parameters = {}
    if not isinstance(parameters, dict):
        errors["parameters"] = "任务参数必须是对象"

    priority = payload.get("priority", 5)
    try:
        priority = int(priority)
    except (TypeError, ValueError):
        errors["priority"] = "优先级必须是整数"

    if errors:
        raise ValidationError(errors)

    return {
        "name": name,
        "task_type": task_type,
        "robot_id": robot_id,
        "priority": priority,
        "parameters": parameters,
    }


def _password_error(min_length: int) -> str:
    return f"密码长度至少为 {min_length} 位"


def validate_user_payload(payload: dict, min_length: int = 6) -> dict:
    errors = {}
    username = str(payload.get("username") or "").strip()
    password = str(payload.get("password") or "")
    role = str(payload.get("role") or "").strip()

    if not username:
        errors["username"] = "用户名不能为空"
    elif len(username) > 100:
        errors["username"] = "长度不能超过 100 个字符"
    if len(password) < min_length:
        errors["password"] = _password_error(min_length)
    if not role:
        errors["role"] = "角色不能为空"

    if errors:
        raise ValidationError(errors)

    _validate_password_complexity(password)

    return {"username": username, "password": password, "role": role}


def validate_bootstrap_admin_payload(payload: dict, min_length: int = 6) -> dict:
    errors = {}
    username = str(payload.get("username") or "").strip()
    password = str(payload.get("password") or "")

    if not username:
        errors["username"] = "用户名不能为空"
    if len(password) < min_length:
        errors["password"] = _password_error(min_length)

    if errors:
        raise ValidationError(errors)

    _validate_password_complexity(password)

    return {"username": username, "password": password}


def validate_password_payload(payload: dict, min_length: int = 6) -> dict:
    password = str(payload.get("password") or "")
    if len(password) < min_length:
        raise ValidationError({"password": _password_error(min_length)})
    return {"password": password}


def validate_robot_payload(payload: dict) -> dict:
    errors = {}
    robot_code = str(payload.get("robot_code") or "").strip()
    name = str(payload.get("name") or "").strip()
    protocol = str(payload.get("protocol") or "mqtt").strip() or "mqtt"
    capabilities = payload.get("capabilities", {})
    metadata = payload.get("metadata", {})

    if not robot_code:
        errors["robot_code"] = "机器人编码不能为空"
    elif len(robot_code) > 50:
        errors["robot_code"] = "长度不能超过 50 个字符"
    if not name:
        errors["name"] = "机器人名称不能为空"
    elif len(name) > 200:
        errors["name"] = "长度不能超过 200 个字符"
    if not isinstance(capabilities, dict):
        errors["capabilities"] = "设备能力必须是对象"
    if not isinstance(metadata, dict):
        errors["metadata"] = "设备元数据必须是对象"

    if errors:
        raise ValidationError(errors)

    return {
        "robot_code": robot_code,
        "name": name,
        "protocol": protocol,
        "capabilities": capabilities,
        "metadata": metadata,
    }


def validate_command_payload(payload: dict) -> dict:
    command = str(payload.get("command") or "").strip()
    params = payload.get("params", {})
    if not command:
        raise ValidationError({"command": "命令不能为空"})
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise ValidationError({"params": "命令参数必须是对象"})
    return {"command": command, "params": params}


def validate_upload_session_payload(payload: dict) -> dict:
    errors = {}
    task_id = str(payload.get("task_id") or "").strip()
    asset_type = str(payload.get("asset_type") or "").strip()
    file_name = str(payload.get("file_name") or "").strip()
    if not task_id:
        errors["task_id"] = "任务 ID 不能为空"
    if not asset_type:
        errors["asset_type"] = "资产类型不能为空"
    if not file_name:
        errors["file_name"] = "文件名不能为空"
    if errors:
        raise ValidationError(errors)
    _validate_path_segment(asset_type, "asset_type", "资产类型不能包含路径分隔符")
    file_name = validate_upload_file_name(file_name)
    return {"task_id": task_id, "asset_type": asset_type, "file_name": file_name}


def validate_legacy_upload_complete_payload(payload: dict) -> dict:
    errors = {}
    upload_session_id = str(payload.get("upload_session_id") or "").strip()
    file_name = str(payload.get("file_name") or "").strip()
    content = payload.get("content")
    sha256 = str(payload.get("sha256") or "").strip()
    metadata = payload.get("metadata", {})
    trigger_analysis = bool(payload.get("trigger_analysis", True))

    if not upload_session_id:
        errors["upload_session_id"] = "上传会话不能为空"
    if not file_name:
        errors["file_name"] = "文件名不能为空"
    if content is None:
        errors["content"] = "上传内容不能为空"
    if not sha256:
        errors["sha256"] = "sha256 不能为空"
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        errors["metadata"] = "元数据必须是对象"
    if errors:
        raise ValidationError(errors)
    return {
        "upload_session_id": upload_session_id,
        "file_name": file_name,
        "content": content,
        "sha256": sha256,
        "metadata": metadata,
        "trigger_analysis": trigger_analysis,
    }


def validate_upload_finalize_payload(payload: dict) -> dict:
    metadata = payload.get("metadata", {})
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise ValidationError({"metadata": "元数据必须是对象"})
    return {"metadata": metadata, "trigger_analysis": bool(payload.get("trigger_analysis", True))}
