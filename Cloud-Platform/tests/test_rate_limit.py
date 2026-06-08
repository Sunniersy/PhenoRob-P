"""Tests for the login rate limiter."""

import time
import threading

import pytest

from backend.app.rate_limit import SlidingWindowRateLimiter, init_limiter, get_limiter


class TestSlidingWindowRateLimiter:
    def test_allows_requests_within_limit(self):
        limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            assert limiter.is_allowed("1.2.3.4") is True

    def test_blocks_requests_over_limit(self):
        limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            limiter.is_allowed("1.2.3.4")
        assert limiter.is_allowed("1.2.3.4") is False

    def test_different_keys_are_independent(self):
        limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60)
        assert limiter.is_allowed("ip-a") is True
        assert limiter.is_allowed("ip-a") is True
        assert limiter.is_allowed("ip-a") is False
        assert limiter.is_allowed("ip-b") is True

    def test_remaining_count(self):
        limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=60)
        assert limiter.remaining("x") == 5
        limiter.is_allowed("x")
        assert limiter.remaining("x") == 4

    def test_retry_after_is_zero_when_allowed(self):
        limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=60)
        assert limiter.retry_after("x") == 0

    def test_retry_after_is_positive_when_blocked(self):
        limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60)
        limiter.is_allowed("x")
        assert limiter.retry_after("x") > 0

    def test_window_expiry_allows_new_requests(self):
        limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=1)
        assert limiter.is_allowed("x") is True
        assert limiter.is_allowed("x") is False
        time.sleep(1.1)
        assert limiter.is_allowed("x") is True

    def test_thread_safety(self):
        limiter = SlidingWindowRateLimiter(max_requests=100, window_seconds=60)

        def hit():
            for _ in range(50):
                limiter.is_allowed("shared-key")

        threads = [threading.Thread(target=hit) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert limiter.remaining("shared-key") == 0

    def test_cleanup_removes_expired_keys(self):
        limiter = SlidingWindowRateLimiter(
            max_requests=5, window_seconds=1, cleanup_interval=0
        )
        limiter.is_allowed("ephemeral")
        assert "ephemeral" in limiter._hits
        time.sleep(1.1)
        # Trigger cleanup by hitting a different key
        limiter.is_allowed("trigger")
        assert "ephemeral" not in limiter._hits


class TestLimiterSingleton:
    def test_init_creates_global_limiter(self):
        # Reset
        import backend.app.rate_limit as rl
        rl._limiter = None

        init_limiter(max_requests=10, window_seconds=300)
        limiter = get_limiter()
        assert limiter is not None
        assert limiter.max_requests == 10
        assert limiter.window_seconds == 300

    def test_get_limiter_returns_none_when_not_initialised(self):
        import backend.app.rate_limit as rl
        rl._limiter = None
        assert get_limiter() is None
