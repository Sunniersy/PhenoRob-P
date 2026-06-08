from datetime import datetime, timezone

from sqlalchemy import desc, func, select

from backend.app.models import RealtimeEvent, SystemAlert, User
from backend.app.pagination import build_paginated_payload
from backend.app.validators import escape_like_wildcards


class SystemService:
    def __init__(self, db, storage, task_queue, transport, realtime, config):
        self.db = db
        self.storage = storage
        self.task_queue = task_queue
        self.transport = transport
        self.realtime = realtime
        self.config = config
        self.app_version = "unknown"

    def health(self) -> dict:
        return {"ok": True, "service": "backend", "mode": "liveness"}

    def bootstrap_check(self) -> dict:
        user_count = self._user_count()
        needs_initial_admin = user_count == 0
        checks = {
            "database": self._check(self.db.ping),
            "minio": self._check(self.storage.healthcheck),
            "redis": self._check(self.task_queue.healthcheck),
            "celery": self._check(self.task_queue.describe),
            "mqtt": self._check(self.transport.healthcheck),
            "websocket": self._check(self.realtime.healthcheck),
        }
        checks_ok = all(item["ok"] for item in checks.values())
        initialization_ok = not needs_initial_admin
        return {
            "ok": checks_ok and initialization_ok,
            "checks_ok": checks_ok,
            "initialization_ok": initialization_ok,
            "needs_initial_admin": needs_initial_admin,
            "user_count": user_count,
            "checks": checks,
        }

    def list_alerts(self, filters: dict | None = None) -> dict:
        filters = filters or {}
        with self.db.session_scope() as session:
            query = select(SystemAlert)
            if filters.get("level"):
                query = query.where(SystemAlert.level == filters["level"])
            if filters.get("status") == "unread":
                query = query.where(SystemAlert.is_acknowledged.is_(False))
            elif filters.get("status") == "acknowledged":
                query = query.where(SystemAlert.is_acknowledged.is_(True))
            if filters.get("q"):
                query = query.where(SystemAlert.message.ilike(f"%{escape_like_wildcards(filters['q'])}%"))
            total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
            alerts = session.scalars(
                query.order_by(desc(SystemAlert.created_at))
                .offset((filters["page"] - 1) * filters["page_size"])
                .limit(filters["page_size"])
            ).all()
            return build_paginated_payload(
                [self.serialize_alert(item) for item in alerts], total, filters["page"], filters["page_size"]
            )

    def acknowledge_alert(self, alert_id: str, username: str, is_acknowledged: bool) -> dict:
        with self.db.session_scope() as session:
            alert = session.get(SystemAlert, alert_id)
            if not alert:
                raise ValueError("alert not found")
            alert.is_acknowledged = is_acknowledged
            alert.acknowledged_by = username if is_acknowledged else None
            alert.acknowledged_at = datetime.now(timezone.utc) if is_acknowledged else None
            session.commit()
            return self.serialize_alert(alert)

    def runtime(self) -> dict:
        with self.db.session_scope() as session:
            runtime_event = session.scalars(
                select(RealtimeEvent).where(RealtimeEvent.event == "system.runtime").order_by(desc(RealtimeEvent.id)).limit(20)
            ).all()
            last_sweep = next((item for item in runtime_event if item.payload.get("name") == "robot_offline_sweep"), None)
            return {
                "version": self.app_version,
                "backends": {
                    "storage": self.storage.describe(),
                    "task_queue": self.task_queue.describe(),
                    "transport": self.transport.describe(),
                    "realtime": {"enabled": self.realtime.enabled},
                },
                "last_offline_sweep_at": last_sweep.timestamp.isoformat() if last_sweep else None,
            }

    def release_readiness(self) -> dict:
        checks = [
            self._readiness_check(
                "application_secrets",
                self._has_release_secrets(),
                "blocker",
                "SECRET_KEY, JWT_SECRET, and BOOTSTRAP_TOKEN must be rotated away from placeholder/demo values",
                {
                    "secret_key": self._secret_state(self.config["SECRET_KEY"]),
                    "jwt_secret": self._secret_state(self.config["JWT_SECRET"]),
                    "bootstrap_token": self._secret_state(self.config["BOOTSTRAP_TOKEN"]),
                },
            ),
            self._readiness_check(
                "bootstrap_token",
                bool(self.config["BOOTSTRAP_TOKEN"]),
                "blocker",
                "BOOTSTRAP_TOKEN must be configured before exposing initial admin bootstrap",
                {"configured": bool(self.config["BOOTSTRAP_TOKEN"])},
            ),
            self._readiness_check(
                "frontend_origin_https",
                str(self.config["FRONTEND_BASE_URL"]).startswith("https://"),
                "blocker",
                "FRONTEND_BASE_URL must use HTTPS in production",
                {"frontend_base_url": self.config["FRONTEND_BASE_URL"]},
            ),
            self._readiness_check(
                "analysis_provider",
                self.config["ANALYSIS_PROVIDER"] == "http" and bool(self.config["ANALYSIS_HTTP_ENDPOINT"]),
                "blocker",
                "Analysis must use the HTTP provider with an explicit endpoint",
                {
                    "analysis_provider": self.config["ANALYSIS_PROVIDER"],
                    "analysis_http_endpoint": bool(self.config["ANALYSIS_HTTP_ENDPOINT"]),
                },
            ),
            self._readiness_check(
                "password_policy",
                int(self.config["PASSWORD_MIN_LENGTH"]) >= 12,
                "blocker",
                "PASSWORD_MIN_LENGTH should be at least 12 for production operators",
                {"password_min_length": self.config["PASSWORD_MIN_LENGTH"]},
            ),
            self._readiness_check(
                "storage_backend",
                self.config["STORAGE_BACKEND"] == "minio",
                "blocker",
                "Object storage should use MinIO/S3-compatible storage instead of container-local disk",
                {"storage_backend": self.config["STORAGE_BACKEND"]},
            ),
            self._readiness_check(
                "transport_backend",
                self.config["TRANSPORT_BACKEND"] == "mqtt",
                "blocker",
                "Robot transport should use MQTT in production",
                {"transport_backend": self.config["TRANSPORT_BACKEND"]},
            ),
            self._readiness_check(
                "mqtt_credentials",
                self._has_mqtt_credentials(),
                "blocker",
                "MQTT username and password must be configured before connecting real robots",
                {
                    "transport_backend": self.config["TRANSPORT_BACKEND"],
                    "username": self._secret_state(self.config.get("MQTT_USERNAME")),
                    "password": self._secret_state(self.config.get("MQTT_PASSWORD")),
                },
            ),
            self._readiness_check(
                "task_queue_backend",
                self.config["TASK_QUEUE_BACKEND"] == "celery",
                "blocker",
                "Background analysis should run on Celery in production",
                {"task_queue_backend": self.config["TASK_QUEUE_BACKEND"]},
            ),
            self._readiness_check(
                "minio_credentials",
                self._has_non_default_minio_credentials(),
                "blocker",
                "MinIO credentials must be rotated away from demo/default values",
                {"storage_backend": self.config["STORAGE_BACKEND"]},
            ),
            self._readiness_check(
                "upload_limit",
                0 < int(self.config["MAX_UPLOAD_SIZE_BYTES"]) <= 32 * 1024 * 1024,
                "warning",
                "Upload payloads should stay within a bounded production limit",
                {"max_upload_size_bytes": self.config["MAX_UPLOAD_SIZE_BYTES"]},
            ),
            self._readiness_check(
                "websocket",
                bool(self.config["WEBSOCKET_ENABLED"]),
                "warning",
                "Realtime websocket notifications are disabled",
                {"websocket_enabled": self.config["WEBSOCKET_ENABLED"]},
            ),
        ]
        blockers = [item for item in checks if item["severity"] == "blocker" and not item["ok"]]
        warnings = [item for item in checks if item["severity"] == "warning" and not item["ok"]]
        return {"ok": not blockers, "checks": checks, "blockers": blockers, "warnings": warnings}

    def _user_count(self) -> int:
        with self.db.session_scope() as session:
            return session.scalar(select(func.count(User.id))) or 0

    @staticmethod
    def serialize_alert(item: SystemAlert) -> dict:
        return {
            "id": item.id,
            "source": item.source,
            "level": item.level,
            "message": item.message,
            "payload": item.payload,
            "is_acknowledged": item.is_acknowledged,
            "acknowledged_by": item.acknowledged_by,
            "acknowledged_at": item.acknowledged_at.isoformat() if item.acknowledged_at else None,
            "created_at": item.created_at.isoformat(),
        }

    @staticmethod
    def _check(callback):
        try:
            details = callback()
            return {"ok": True, "details": details or {}}
        except Exception as exc:
            return {"ok": False, "details": {"state": "disconnected", "error": str(exc)}}

    @staticmethod
    def _readiness_check(key: str, ok: bool, severity: str, message: str, details: dict | None = None) -> dict:
        return {
            "key": key,
            "ok": ok,
            "severity": severity,
            "message": message,
            "details": details or {},
        }

    def _has_non_default_minio_credentials(self) -> bool:
        if self.config["STORAGE_BACKEND"] != "minio":
            return True
        return not self._looks_placeholder_or_demo_secret(
            self.config["MINIO_ACCESS_KEY"]
        ) and not self._looks_placeholder_or_demo_secret(self.config["MINIO_SECRET_KEY"])

    def _has_release_secrets(self) -> bool:
        return all(
            not self._looks_placeholder_or_demo_secret(self.config[key])
            for key in ("SECRET_KEY", "JWT_SECRET", "BOOTSTRAP_TOKEN")
        )

    def _has_mqtt_credentials(self) -> bool:
        if self.config["TRANSPORT_BACKEND"] != "mqtt":
            return True
        return not self._looks_placeholder_or_demo_secret(
            self.config.get("MQTT_USERNAME")
        ) and not self._looks_placeholder_or_demo_secret(self.config.get("MQTT_PASSWORD"))

    @staticmethod
    def _looks_placeholder_or_demo_secret(value: str | None) -> bool:
        normalized = str(value or "").strip().lower()
        if not normalized:
            return True
        return (
            normalized in {"change-me", "change-me-too"}
            or normalized.startswith("replace-with-")
            or "demo" in normalized
            or "compose-only" in normalized
        )

    @classmethod
    def _secret_state(cls, value: str | None) -> str:
        return "unsafe" if cls._looks_placeholder_or_demo_secret(value) else "configured"
