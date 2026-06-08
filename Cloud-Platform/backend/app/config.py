import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
if not Path("/.dockerenv").exists() and "DOCKER_CONTAINER" not in os.environ:
    load_dotenv(BASE_DIR / ".env", override=False)


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


class Config:
    SUPPORTED_ANALYSIS_PROVIDERS = {"disabled", "demo", "http"}
    SUPPORTED_STORAGE_BACKENDS = {"local", "minio"}
    SUPPORTED_TASK_QUEUE_BACKENDS = {"inline", "celery"}
    SUPPORTED_TRANSPORT_BACKENDS = {"memory", "mqtt"}

    APP_ENV = os.getenv("APP_ENV", "production")
    DEBUG = _bool("FLASK_DEBUG", False)
    TESTING = False
    ALLOW_RUNTIME_FALLBACK = _bool("ALLOW_RUNTIME_FALLBACK", False)
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "5000"))
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")
    FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    JWT_SECRET = os.getenv("JWT_SECRET", "change-me-too")
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/phenobot")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
    MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
    MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", f"cloud-server-{os.getenv('HOSTNAME', 'local')}")
    MQTT_QOS = int(os.getenv("MQTT_QOS", "1"))
    TRANSPORT_BACKEND = os.getenv("TRANSPORT_BACKEND", "mqtt")
    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "minio")
    TASK_QUEUE_BACKEND = os.getenv("TASK_QUEUE_BACKEND", "celery")
    TASK_QUEUE_EAGER = _bool("TASK_QUEUE_EAGER", False)
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET = os.getenv("MINIO_BUCKET", "phenobot-assets")
    MINIO_SECURE = _bool("MINIO_SECURE", False)
    LOCAL_STORAGE_PATH = os.getenv("LOCAL_STORAGE_PATH", str(BASE_DIR / "storage"))
    WEBSOCKET_ENABLED = _bool("WEBSOCKET_ENABLED", True)
    ANALYSIS_LATENCY_SECONDS = int(os.getenv("ANALYSIS_LATENCY_SECONDS", "1"))
    ANALYSIS_PROVIDER = os.getenv("ANALYSIS_PROVIDER", "disabled")
    ROBOT_OFFLINE_TTL_SECONDS = int(os.getenv("ROBOT_OFFLINE_TTL_SECONDS", "30"))
    MQTT_PROTOCOL_VERSION = os.getenv("MQTT_PROTOCOL_VERSION", "1.0")
    APP_VERSION = os.getenv("APP_VERSION", "0.2.0")
    ANALYSIS_HTTP_ENDPOINT = os.getenv("ANALYSIS_HTTP_ENDPOINT", "")
    ANALYSIS_HTTP_TOKEN = os.getenv("ANALYSIS_HTTP_TOKEN", "")
    BOOTSTRAP_TOKEN = os.getenv("BOOTSTRAP_TOKEN", "")
    PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "12"))
    MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(32 * 1024 * 1024)))
    RATE_LIMIT_REFRESH_MAX = int(os.getenv("RATE_LIMIT_REFRESH_MAX", "20"))
    RATE_LIMIT_REFRESH_WINDOW = int(os.getenv("RATE_LIMIT_REFRESH_WINDOW", "60"))
    RATE_LIMIT_CREATE_USER_MAX = int(os.getenv("RATE_LIMIT_CREATE_USER_MAX", "10"))
    RATE_LIMIT_CREATE_USER_WINDOW = int(os.getenv("RATE_LIMIT_CREATE_USER_WINDOW", "60"))
    RATE_LIMIT_LOGIN_MAX = int(os.getenv("RATE_LIMIT_LOGIN_MAX", "10"))
    RATE_LIMIT_LOGIN_WINDOW = int(os.getenv("RATE_LIMIT_LOGIN_WINDOW", "300"))
    RATE_LIMIT_LOGIN_ENABLED = _bool("RATE_LIMIT_LOGIN_ENABLED", True)
    REALTIME_EVENT_TTL_HOURS = int(os.getenv("REALTIME_EVENT_TTL_HOURS", "24"))
    SYSTEM_ALERT_ACK_TTL_DAYS = int(os.getenv("SYSTEM_ALERT_ACK_TTL_DAYS", "7"))

    def __init__(self):
        self.MAX_CONTENT_LENGTH = self.MAX_UPLOAD_SIZE_BYTES
        self._validate_runtime_options()
        self._validate_runtime_safety()

    def _validate_runtime_options(self) -> None:
        self._validate_choice("ANALYSIS_PROVIDER", self.ANALYSIS_PROVIDER, self.SUPPORTED_ANALYSIS_PROVIDERS)
        self._validate_choice("STORAGE_BACKEND", self.STORAGE_BACKEND, self.SUPPORTED_STORAGE_BACKENDS)
        self._validate_choice("TASK_QUEUE_BACKEND", self.TASK_QUEUE_BACKEND, self.SUPPORTED_TASK_QUEUE_BACKENDS)
        self._validate_choice("TRANSPORT_BACKEND", self.TRANSPORT_BACKEND, self.SUPPORTED_TRANSPORT_BACKENDS)

        if self.ANALYSIS_PROVIDER == "http" and not self.ANALYSIS_HTTP_ENDPOINT:
            raise ValueError("ANALYSIS_HTTP_ENDPOINT is required when ANALYSIS_PROVIDER=http")
        if self.PASSWORD_MIN_LENGTH < 6:
            raise ValueError("PASSWORD_MIN_LENGTH must be at least 6")
        if self.MAX_UPLOAD_SIZE_BYTES <= 0:
            raise ValueError("MAX_UPLOAD_SIZE_BYTES must be positive")

    def _is_development_mode(self) -> bool:
        if self.DEBUG or self.TESTING:
            return True

        return str(self.APP_ENV).lower() in {"development", "dev", "local"}

    _MIN_SECRET_LENGTH = 16
    _WEAK_SECRET_PREFIXES = ("replace-with-", "demo-", "test-", "example-")

    def _validate_runtime_safety(self) -> None:
        if self._is_development_mode():
            return
        if self.ALLOW_RUNTIME_FALLBACK:
            return

        # --- secret key checks ---
        if self._is_placeholder_secret(self.SECRET_KEY) or self._is_placeholder_secret(self.JWT_SECRET):
            raise ValueError("production mode requires non-placeholder SECRET_KEY and JWT_SECRET")

        for name, value in [("SECRET_KEY", self.SECRET_KEY), ("JWT_SECRET", self.JWT_SECRET)]:
            if len(value) < self._MIN_SECRET_LENGTH:
                raise ValueError(
                    f"production mode requires {name} to be at least "
                    f"{self._MIN_SECRET_LENGTH} characters"
                )

        if self.FRONTEND_BASE_URL == "*" or not self.FRONTEND_BASE_URL.startswith(("http://", "https://")):
            raise ValueError("FRONTEND_BASE_URL must be an explicit http(s) origin in production mode")
        if self._is_placeholder_secret(self.BOOTSTRAP_TOKEN):
            raise ValueError("production mode requires non-placeholder BOOTSTRAP_TOKEN")
        if self.PASSWORD_MIN_LENGTH < 12:
            raise ValueError("production mode requires PASSWORD_MIN_LENGTH >= 12")

        # --- default credential checks ---
        if self.STORAGE_BACKEND == "minio":
            default_minio_credentials = {
                ("minioadmin", "minioadmin"),
                ("replace-with-minio-access-key", "replace-with-minio-secret-key"),
            }
            if (self.MINIO_ACCESS_KEY, self.MINIO_SECRET_KEY) in default_minio_credentials:
                raise ValueError("production mode requires non-default MinIO credentials")

        if ":postgres@" in self.DATABASE_URL:
            raise ValueError(
                "production mode requires a non-default database password "
                "(change 'postgres:postgres' in DATABASE_URL)"
            )

    @staticmethod
    def _validate_choice(name: str, value: str, allowed: set[str]) -> None:
        if value not in allowed:
            allowed_values = ", ".join(sorted(allowed))
            raise ValueError(f"{name} must be one of: {allowed_values}")

    def _is_placeholder_secret(self, value: str | None) -> bool:
        normalized = str(value or "").strip().lower()
        if not normalized:
            return True
        if normalized in {"change-me", "change-me-too"}:
            return True
        return any(normalized.startswith(p) for p in self._WEAK_SECRET_PREFIXES)


class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    ALLOW_RUNTIME_FALLBACK = True
    DATABASE_URL = "sqlite://"
    TRANSPORT_BACKEND = "memory"
    STORAGE_BACKEND = "local"
    TASK_QUEUE_BACKEND = "inline"
    TASK_QUEUE_EAGER = True
    LOCAL_STORAGE_PATH = str(BASE_DIR / "storage" / "test")
    WEBSOCKET_ENABLED = False
    ANALYSIS_LATENCY_SECONDS = 0
    ANALYSIS_PROVIDER = "disabled"
    SECRET_KEY = "test-secret-key-with-safe-length-32"
    JWT_SECRET = "test-jwt-secret-key-with-safe-length-32"
    BOOTSTRAP_TOKEN = ""
    PASSWORD_MIN_LENGTH = 6
    MAX_UPLOAD_SIZE_BYTES = 32 * 1024 * 1024
    RATE_LIMIT_LOGIN_ENABLED = False
