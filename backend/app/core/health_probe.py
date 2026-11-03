import asyncio
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from sqlalchemy import text

from app.core.logging import mask_secrets
from app.core.redis import redis_client
from app.db.session import engine
from app.schemas.health import ComponentStatus, HealthReadyResponse

logger = logging.getLogger("app.health")


class ReadinessAdmissionController:
    """Bounded admission controller and executor for readiness probes.

    Permits at most 2 concurrent readiness requests per API process. Saturated
    requests return HTTP 503 immediately without submitting blocking work.
    """

    def __init__(self, max_concurrent: int = 2) -> None:
        self.max_concurrent = max_concurrent
        self._current_permits = 0
        self._lock = threading.Lock()
        self._executor: ThreadPoolExecutor | None = None

    @property
    def executor(self) -> ThreadPoolExecutor:
        """Provide or re-instantiate active threadpool executor."""
        with self._lock:
            if self._executor is None or getattr(self._executor, "_shutdown", False):
                self._executor = ThreadPoolExecutor(
                    max_workers=4, thread_name_prefix="health_probe"
                )
            return self._executor

    def acquire_permit(self) -> bool:
        """Attempt to acquire an admission permit. Returns False if saturated."""
        with self._lock:
            if self._current_permits >= self.max_concurrent:
                return False
            self._current_permits += 1
            return True

    def release_permit(self) -> None:
        """Release an admission permit idempotently."""
        with self._lock:
            if self._current_permits > 0:
                self._current_permits -= 1

    @property
    def current_load(self) -> int:
        with self._lock:
            return self._current_permits

    def shutdown(self) -> None:
        """Shut down the probe executor cleanly."""
        with self._lock:
            if self._executor is not None:
                self._executor.shutdown(wait=False, cancel_futures=True)
                self._executor = None


admission_controller = ReadinessAdmissionController(max_concurrent=2)


def probe_postgres() -> ComponentStatus:
    """Execute synchronous SELECT 1 probe against PostgreSQL with statement timeout."""
    start = time.perf_counter()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency = round((time.perf_counter() - start) * 1000.0, 2)
        return ComponentStatus(
            name="postgres",
            status="connected",
            latency_ms=latency,
            error=None,
        )
    except Exception as exc:
        latency = round((time.perf_counter() - start) * 1000.0, 2)
        sanitized = mask_secrets(str(exc))
        logger.warning("PostgreSQL readiness probe failed: %s", sanitized)
        return ComponentStatus(
            name="postgres",
            status="disconnected",
            latency_ms=latency,
            error="Connection or query failed",
        )


def probe_redis() -> ComponentStatus:
    """Execute synchronous PING probe against Redis with socket timeouts."""
    start = time.perf_counter()
    try:
        pong = redis_client.ping()
        if not pong:
            raise RuntimeError("Redis PING did not return True")
        latency = round((time.perf_counter() - start) * 1000.0, 2)
        return ComponentStatus(
            name="redis",
            status="connected",
            latency_ms=latency,
            error=None,
        )
    except Exception as exc:
        latency = round((time.perf_counter() - start) * 1000.0, 2)
        sanitized = mask_secrets(str(exc))
        logger.warning("Redis readiness probe failed: %s", sanitized)
        return ComponentStatus(
            name="redis",
            status="disconnected",
            latency_ms=latency,
            error="Connection or ping failed",
        )


async def execute_readiness_probe() -> tuple[HealthReadyResponse, int]:
    """Execute concurrent readiness checks with strict admission control."""
    if not admission_controller.acquire_permit():
        logger.warning("Readiness probe saturated (exceeded admission limit)")
        now = datetime.now(UTC)
        return (
            HealthReadyResponse(
                status="unhealthy",
                timestamp=now,
                components={
                    "postgres": ComponentStatus(
                        name="postgres",
                        status="disconnected",
                        error="Admission limit exceeded",
                    ),
                    "redis": ComponentStatus(
                        name="redis",
                        status="disconnected",
                        error="Admission limit exceeded",
                    ),
                },
            ),
            503,
        )

    loop = asyncio.get_running_loop()
    try:
        # Run postgres and redis probes concurrently in the dedicated threadpool
        postgres_future = loop.run_in_executor(admission_controller.executor, probe_postgres)
        redis_future = loop.run_in_executor(admission_controller.executor, probe_redis)

        postgres_status, redis_status = await asyncio.gather(postgres_future, redis_future)
    finally:
        admission_controller.release_permit()

    now = datetime.now(UTC)
    all_connected = postgres_status.status == "connected" and redis_status.status == "connected"

    response = HealthReadyResponse(
        status="ready" if all_connected else "unhealthy",
        timestamp=now,
        components={
            "postgres": postgres_status,
            "redis": redis_status,
        },
    )
    http_code = 200 if all_connected else 503
    return response, http_code
