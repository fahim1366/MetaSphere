import os
import subprocess
import sys
import time
import uuid
from datetime import UTC, datetime

import pytest
from app.core.config import settings

from tests.integration.test_hybrid_dev import is_port_open


@pytest.mark.integration
def test_celery_worker_real_roundtrip() -> None:
    """Verify an end-to-end task roundtrip through a real Celery worker process and Redis."""
    if not is_port_open(settings.REDIS_HOST, settings.REDIS_PORT):
        pytest.skip(
            f"Redis not reachable at {settings.REDIS_HOST}:{settings.REDIS_PORT}. "
            "Start containers with: docker compose -f infrastructure/docker-compose.yml up -d"
        )

    from app.jobs.tasks import health_check_task

    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # Launch actual Celery worker subprocess with Windows-compatible 'solo' pool
    cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "app.jobs.celery_app.celery_app",
        "worker",
        "--pool=solo",
        "-l",
        "info",
    ]

    worker_proc = subprocess.Popen(
        cmd,
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Give worker process 2 seconds to connect to broker
        time.sleep(2.0)

        ping_id = str(uuid.uuid4())
        sent_at = datetime.now(UTC).isoformat()

        start_time = time.perf_counter()
        async_result = health_check_task.delay(ping_id, sent_at)

        # Retrieve result with bounded timeout
        result = async_result.get(timeout=3.0)
        roundtrip_time = time.perf_counter() - start_time

        assert result is not None
        assert result["ping_id"] == ping_id
        assert result["status"] == "pong"
        assert roundtrip_time < 2.0, (
            f"Task roundtrip took {roundtrip_time:.2f}s, exceeding target < 2.0s"
        )
    finally:
        worker_proc.terminate()
        try:
            worker_proc.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            worker_proc.kill()
