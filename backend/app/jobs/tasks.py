import socket
import time
from datetime import UTC, datetime
from typing import Any

from app.jobs.celery_app import celery_app


@celery_app.task(name="app.jobs.tasks.health_check_task", bind=True)
def health_check_task(self: Any, ping_id: str, sent_at: str) -> dict[str, Any]:
    """Baseline asynchronous Celery verification task.

    Validates that a task can be queued, consumed by a worker, executed, and its
    result stored in the Redis backend in accordance with contracts/celery-task.json.
    """
    start_time = time.perf_counter()
    now_utc = datetime.now(UTC).isoformat()
    duration_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

    worker_node = getattr(self.request, "hostname", None) or socket.gethostname()

    return {
        "ping_id": ping_id,
        "status": "pong",
        "worker_name": str(worker_node),
        "completed_at": now_utc,
        "duration_ms": max(0.0, duration_ms),
    }
