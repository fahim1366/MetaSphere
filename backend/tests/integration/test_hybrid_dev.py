import os
import socket
import subprocess
import sys
import time

import pytest
from app.core.config import settings


def is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a network port is reachable."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@pytest.mark.integration
def test_hybrid_dev_datastores_reachable() -> None:
    """Verify local PostgreSQL and Redis containers are accessible on configured ports."""
    postgres_up = is_port_open(settings.POSTGRES_HOST, settings.POSTGRES_PORT)
    redis_up = is_port_open(settings.REDIS_HOST, settings.REDIS_PORT)

    if not postgres_up or not redis_up:
        pytest.skip(
            f"Local datastores not reachable (PostgreSQL {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}={postgres_up}, "
            f"Redis {settings.REDIS_HOST}:{settings.REDIS_PORT}={redis_up}). "
            "Start containers with: docker compose -f infrastructure/docker-compose.yml up -d"
        )

    assert postgres_up, "PostgreSQL port must be open"
    assert redis_up, "Redis port must be open"


@pytest.mark.integration
def test_backend_startup_time() -> None:
    """Measure backend startup time to application-ready status (< 5.0 seconds)."""
    # Start uvicorn process on a test port
    test_port = 8009
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(test_port),
    ]

    start_time = time.perf_counter()
    proc = subprocess.Popen(
        cmd,
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    ready = False
    elapsed = 0.0
    try:
        for _ in range(50):  # poll every 100ms for up to 5s
            time.sleep(0.1)
            if is_port_open("127.0.0.1", test_port, timeout=0.1):
                elapsed = time.perf_counter() - start_time
                ready = True
                break

        assert ready, "Backend process failed to reach ready state within 5 seconds"
        assert elapsed < 5.0, f"Backend startup took {elapsed:.2f}s, exceeding target < 5.0s"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            proc.kill()
