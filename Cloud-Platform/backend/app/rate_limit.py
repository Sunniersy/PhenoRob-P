"""In-memory sliding-window rate limiter for protecting sensitive endpoints."""

import logging
import time
import threading
from collections import defaultdict
from functools import wraps

from flask import jsonify, request

logger = logging.getLogger(__name__)


class SlidingWindowRateLimiter:
    """Thread-safe sliding-window rate limiter keyed by client IP.

    Parameters
    ----------
    max_requests : int
        Maximum number of requests allowed within the window.
    window_seconds : int
        Length of the sliding window in seconds.
    cleanup_interval : int
        How often (in seconds) to purge expired entries to prevent
        unbounded memory growth.
    """

    def __init__(
        self,
        max_requests: int = 10,
        window_seconds: int = 300,
        cleanup_interval: int = 60,
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.cleanup_interval = cleanup_interval

        # {key: [timestamp, ...]}
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()
        self._last_cleanup = time.monotonic()

    # -- public API ---------------------------------------------------------

    def is_allowed(self, key: str) -> bool:
        """Return ``True`` if *key* has not exceeded the rate limit."""
        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            self._maybe_cleanup(now)
            timestamps = self._hits[key]
            # Drop timestamps outside the window.
            self._hits[key] = [t for t in timestamps if t > cutoff]

            if len(self._hits[key]) >= self.max_requests:
                return False

            self._hits[key].append(now)
            return True

    def remaining(self, key: str) -> int:
        """Return how many requests *key* can still make in the current window."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            active = sum(1 for t in self._hits.get(key, ()) if t > cutoff)
            return max(0, self.max_requests - active)

    def retry_after(self, key: str) -> int:
        """Return seconds until *key* can make another request."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            timestamps = [t for t in self._hits.get(key, ()) if t > cutoff]
            if not timestamps or len(timestamps) < self.max_requests:
                return 0
            oldest = min(timestamps)
            return max(1, int(oldest + self.window_seconds - now) + 1)

    # -- internals ----------------------------------------------------------

    def _maybe_cleanup(self, now: float) -> None:
        """Remove keys whose every timestamp has expired."""
        if now - self._last_cleanup < self.cleanup_interval:
            return
        self._last_cleanup = now
        cutoff = now - self.window_seconds
        stale_keys = [
            k for k, ts in self._hits.items() if not ts or ts[-1] <= cutoff
        ]
        for k in stale_keys:
            del self._hits[k]
        if stale_keys:
            logger.debug("rate-limit cleanup removed %d expired keys", len(stale_keys))


# ---------------------------------------------------------------------------
# Module-level singleton -- configured once from app config via ``init_app``.
# ---------------------------------------------------------------------------
_limiter: SlidingWindowRateLimiter | None = None
_init_lock = threading.Lock()


def init_limiter(max_requests: int, window_seconds: int) -> None:
    """Create (or re-create) the global limiter singleton."""
    global _limiter
    with _init_lock:
        _limiter = SlidingWindowRateLimiter(
            max_requests=max_requests,
            window_seconds=window_seconds,
        )
    logger.info(
        "rate limiter initialised: max_requests=%d window=%ds",
        max_requests,
        window_seconds,
    )


def get_limiter() -> SlidingWindowRateLimiter | None:
    """Return the global limiter (``None`` if not initialised)."""
    return _limiter


# ---------------------------------------------------------------------------
# Flask decorator / helper
# ---------------------------------------------------------------------------

def rate_limit_login(func):
    """Decorator that applies login rate-limiting based on client IP.

    When the limiter is not initialised (e.g. in testing with rate-limiting
    disabled) the request passes through without restriction.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        limiter = get_limiter()
        if limiter is None:
            return func(*args, **kwargs)

        client_ip = request.remote_addr or "unknown"
        if limiter.is_allowed(client_ip):
            return func(*args, **kwargs)

        retry = limiter.retry_after(client_ip)
        logger.warning(
            "login rate-limit exceeded for ip=%s (retry_after=%ds)",
            client_ip,
            retry,
        )
        payload = {
            "message": "too many login attempts, please try again later",
            "data": None,
            "errors": {},
        }
        resp = jsonify(payload), 429
        resp[0].headers["Retry-After"] = str(retry)
        return resp

    return wrapper


# ---------------------------------------------------------------------------
# Named limiter registry -- allows multiple independently-configured limiters.
# ---------------------------------------------------------------------------

_named_limiters: dict[str, SlidingWindowRateLimiter] = {}


def clear_limiters() -> None:
    """Reset all rate limiter singletons (useful when rate-limiting is disabled)."""
    global _limiter, _named_limiters
    with _init_lock:
        _limiter = None
        _named_limiters = {}


def init_named_limiter(name: str, max_requests: int, window_seconds: int) -> None:
    """Create (or re-create) a named rate limiter in the global registry."""
    global _named_limiters
    with _init_lock:
        _named_limiters[name] = SlidingWindowRateLimiter(
            max_requests=max_requests,
            window_seconds=window_seconds,
        )
    logger.info(
        "named rate limiter '%s' initialised: max_requests=%d window=%ds",
        name,
        max_requests,
        window_seconds,
    )


def get_named_limiter(name: str) -> SlidingWindowRateLimiter | None:
    """Return a named rate limiter (``None`` if not initialised)."""
    return _named_limiters.get(name)


def rate_limit(limiter_name: str, message: str = "too many requests, please try again later"):
    """Decorator factory for rate-limiting based on client IP using a named limiter.

    When the named limiter is not initialised (e.g. in testing with rate-limiting
    disabled) the request passes through without restriction.

    Usage::

        @bp.post("/some-endpoint")
        @rate_limit("refresh")
        def my_view(): ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter = get_named_limiter(limiter_name)
            if limiter is None:
                return func(*args, **kwargs)

            client_ip = request.remote_addr or "unknown"
            if limiter.is_allowed(client_ip):
                return func(*args, **kwargs)

            retry = limiter.retry_after(client_ip)
            logger.warning(
                "rate-limit exceeded for ip=%s limiter=%s (retry_after=%ds)",
                client_ip,
                limiter_name,
                retry,
            )
            payload = {
                "message": message,
                "data": None,
                "errors": {},
            }
            resp = jsonify(payload), 429
            resp[0].headers["Retry-After"] = str(retry)
            return resp

        return wrapper

    return decorator
