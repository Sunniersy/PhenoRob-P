"""One-time download token service to prevent JWT leakage in URLs.

Instead of passing JWT tokens via query strings (which leak into server logs,
browser history, and proxy logs), clients exchange their JWT for a short-lived
one-time download token via POST /api/downloads/token, then use that token to
download files.

Uses Redis when available for cross-worker token visibility, falls back to
in-memory storage for single-process deployments.
"""

import json
import logging
import threading
import time
import uuid

logger = logging.getLogger(__name__)


class DownloadTokenService:
    """Manages one-time download tokens with TTL.

    When a Redis URL is provided and reachable, tokens are stored in Redis
    so they are visible across all Celery workers.  Otherwise an in-memory
    dict is used (backward-compatible single-process mode).
    """

    DEFAULT_TTL_SECONDS = 600

    def __init__(
        self,
        redis_url: str | None = None,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ):
        self._ttl = ttl_seconds
        self._redis = None

        # -- in-memory fallback state --
        self._tokens: dict[str, dict] = {}
        self._lock = threading.Lock()

        if redis_url:
            try:
                import redis as redis_lib

                self._redis = redis_lib.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=3,
                )
                self._redis.ping()
                logger.info(
                    json.dumps(
                        {
                            "event": "download_token_service_init",
                            "backend": "redis",
                            "ttl_seconds": ttl_seconds,
                        },
                        ensure_ascii=False,
                    )
                )
            except Exception as exc:
                logger.warning(
                    json.dumps(
                        {
                            "event": "download_token_service_fallback",
                            "backend": "memory",
                            "reason": str(exc),
                        },
                        ensure_ascii=False,
                    )
                )
                self._redis = None
        else:
            logger.info(
                json.dumps(
                    {
                        "event": "download_token_service_init",
                        "backend": "memory",
                        "ttl_seconds": ttl_seconds,
                    },
                    ensure_ascii=False,
                )
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_token(self, user_id: int, resource_path: str) -> str:
        """Create a one-time download token bound to a specific resource path."""
        token = uuid.uuid4().hex
        created_at = time.time()
        metadata = {
            "user_id": user_id,
            "resource_path": resource_path,
            "created_at": created_at,
        }

        if self._redis:
            try:
                key = f"download_token:{token}"
                self._redis.set(key, json.dumps(metadata), ex=self._ttl)
                logger.info(
                    json.dumps(
                        {
                            "event": "token_created",
                            "backend": "redis",
                            "token_prefix": token[:8],
                            "user_id": user_id,
                            "resource_path": resource_path,
                        },
                        ensure_ascii=False,
                    )
                )
                return token
            except Exception as exc:
                logger.error(
                    json.dumps(
                        {
                            "event": "token_create_error",
                            "backend": "redis",
                            "error": str(exc),
                            "user_id": user_id,
                        },
                        ensure_ascii=False,
                    )
                )
                # Fall through to memory storage so the request is not lost.

        # -- memory storage --
        expires_at = time.monotonic() + self._ttl
        with self._lock:
            self._cleanup_expired()
            self._tokens[token] = {
                **metadata,
                "expires_at": expires_at,
            }
        logger.info(
            json.dumps(
                {
                    "event": "token_created",
                    "backend": "memory",
                    "token_prefix": token[:8],
                    "user_id": user_id,
                    "resource_path": resource_path,
                },
                ensure_ascii=False,
            )
        )
        return token

    def consume_token(self, token: str, resource_path: str) -> int | None:
        """Validate and consume a one-time token.

        Returns ``user_id`` if the token is valid, ``None`` otherwise.
        The token is removed after consumption (single-use) and must match
        the resource path it was created for.
        """
        if self._redis:
            try:
                return self._consume_from_redis(token, resource_path)
            except Exception as exc:
                logger.error(
                    json.dumps(
                        {
                            "event": "token_consume_error",
                            "backend": "redis",
                            "error": str(exc),
                            "token_prefix": token[:8] if token else "",
                        },
                        ensure_ascii=False,
                    )
                )
                # Fall through to memory (token likely not there, but try).

        return self._consume_from_memory(token, resource_path)

    # ------------------------------------------------------------------
    # Redis helpers
    # ------------------------------------------------------------------

    def _consume_from_redis(self, token: str, resource_path: str) -> int | None:
        """Atomically get-and-delete a token from Redis."""
        key = f"download_token:{token}"
        raw = self._redis.getdel(key)  # atomic GET + DEL
        if raw is None:
            logger.info(
                json.dumps(
                    {
                        "event": "token_consume_miss",
                        "backend": "redis",
                        "token_prefix": token[:8] if token else "",
                    },
                    ensure_ascii=False,
                )
            )
            return None

        try:
            metadata = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning(
                json.dumps(
                    {
                        "event": "token_consume_corrupt",
                        "backend": "redis",
                        "token_prefix": token[:8],
                    },
                    ensure_ascii=False,
                )
            )
            return None

        if metadata.get("resource_path") != resource_path:
            logger.warning(
                json.dumps(
                    {
                        "event": "token_consume_path_mismatch",
                        "backend": "redis",
                        "token_prefix": token[:8],
                        "expected": resource_path,
                        "actual": metadata.get("resource_path"),
                    },
                    ensure_ascii=False,
                )
            )
            return None

        user_id = metadata.get("user_id")
        logger.info(
            json.dumps(
                {
                    "event": "token_consumed",
                    "backend": "redis",
                    "token_prefix": token[:8],
                    "user_id": user_id,
                },
                ensure_ascii=False,
            )
        )
        return user_id

    # ------------------------------------------------------------------
    # Memory helpers
    # ------------------------------------------------------------------

    def _consume_from_memory(self, token: str, resource_path: str) -> int | None:
        with self._lock:
            self._cleanup_expired()
            entry = self._tokens.pop(token, None)
        if entry is None:
            logger.info(
                json.dumps(
                    {
                        "event": "token_consume_miss",
                        "backend": "memory",
                        "token_prefix": token[:8] if token else "",
                    },
                    ensure_ascii=False,
                )
            )
            return None
        if entry["expires_at"] < time.monotonic():
            return None
        if entry["resource_path"] != resource_path:
            logger.warning(
                json.dumps(
                    {
                        "event": "token_consume_path_mismatch",
                        "backend": "memory",
                        "token_prefix": token[:8],
                    },
                    ensure_ascii=False,
                )
            )
            return None

        logger.info(
            json.dumps(
                {
                    "event": "token_consumed",
                    "backend": "memory",
                    "token_prefix": token[:8],
                    "user_id": entry["user_id"],
                },
                ensure_ascii=False,
            )
        )
        return entry["user_id"]

    def _cleanup_expired(self) -> None:
        """Remove expired tokens to prevent memory leaks."""
        now = time.monotonic()
        expired = [k for k, v in self._tokens.items() if v["expires_at"] < now]
        for k in expired:
            del self._tokens[k]
