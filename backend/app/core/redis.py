from __future__ import annotations

import redis

from app.core.config import ApplicationSettings, settings


def get_redis_client(
    app_settings: ApplicationSettings | None = None,
) -> redis.Redis[str]:
    """Create a Redis client instance configured with bounded driver-level socket timeouts."""
    cfg = app_settings or settings
    return redis.Redis(
        host=cfg.REDIS_HOST,
        port=cfg.REDIS_PORT,
        db=cfg.REDIS_DB,
        socket_connect_timeout=cfg.REDIS_CONNECT_TIMEOUT,
        socket_timeout=cfg.REDIS_SOCKET_TIMEOUT,
        decode_responses=True,
    )


# Default client instance
redis_client: redis.Redis[str] = get_redis_client(settings)
