import contextlib
import time

from app.core.config import settings
from app.core.redis import redis_client


def is_login_rate_limited(identifier: str) -> bool:
    """Check if an IP address or username has exceeded the allowed failed login rate."""
    if settings.APP_ENV == "test":
        return False

    key = f"rate_limit:login:{identifier}"
    now = time.time()
    window_seconds = settings.AUTH_LOCKOUT_MINUTES * 60

    try:
        # Use Redis sorted set for sliding window
        pipe = redis_client.pipeline()
        # Remove attempts older than the window
        pipe.zremrangebyscore(key, 0, now - window_seconds)
        # Count remaining attempts
        pipe.zcard(key)
        results = pipe.execute()
        attempt_count = results[1]
        return bool(attempt_count >= settings.AUTH_MAX_FAILED_ATTEMPTS)
    except Exception:
        # If Redis is unavailable, do not block users; fail open for rate-limiter
        return False


def record_failed_login_attempt(identifier: str) -> None:
    """Record a failed login attempt in the sliding window."""
    if settings.APP_ENV == "test":
        return

    key = f"rate_limit:login:{identifier}"
    now = time.time()
    window_seconds = settings.AUTH_LOCKOUT_MINUTES * 60

    try:
        pipe = redis_client.pipeline()
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window_seconds)
        pipe.execute()
    except Exception:
        pass


def clear_failed_login_attempts(identifier: str) -> None:
    """Clear failed login attempts upon successful authentication."""
    if settings.APP_ENV == "test":
        return

    key = f"rate_limit:login:{identifier}"
    with contextlib.suppress(Exception):
        redis_client.delete(key)
