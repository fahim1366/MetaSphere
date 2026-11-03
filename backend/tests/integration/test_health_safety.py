import time

import pytest
from app.core.config import ApplicationSettings
from app.core.health_probe import admission_controller, probe_postgres
from app.core.redis import get_redis_client
from app.main import app
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_redis_timeout_configuration() -> None:
    """Verify Redis client is initialized with exact bounded 2.0s timeouts."""
    client = get_redis_client()
    connection_kwargs = client.connection_pool.connection_kwargs
    assert connection_kwargs.get("socket_timeout") == 2.0
    assert connection_kwargs.get("socket_connect_timeout") == 2.0


@pytest.mark.integration
def test_admission_burst_saturation() -> None:
    """Verify that bursts exceeding 2 permits immediately receive 503 without queueing."""
    with TestClient(app) as client:
        # Acquire all permits
        assert admission_controller.acquire_permit() is True
        assert admission_controller.acquire_permit() is True
        assert admission_controller.acquire_permit() is False

        # Attempt readiness request while saturated
        start = time.perf_counter()
        response = client.get("/health/ready")
        duration = time.perf_counter() - start

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert duration < 0.1, "Saturated probe should reject immediately (< 100ms)"

        # Release permits
        admission_controller.release_permit()
        admission_controller.release_permit()
        assert admission_controller.current_load == 0


@pytest.mark.integration
def test_blackholed_datastore_failure_detection() -> None:
    """Verify connecting to an invalid port fails within bounded timeout (< 3s)."""
    bad_settings = ApplicationSettings(
        POSTGRES_PORT=54329,
        POSTGRES_HOST="127.0.0.1",
        DB_CONNECT_TIMEOUT=2,
    )
    from app.db.session import create_db_engine

    bad_engine = create_db_engine(bad_settings)

    start = time.perf_counter()
    from unittest.mock import patch

    with patch("app.core.health_probe.engine", bad_engine):
        status = probe_postgres()

    duration = time.perf_counter() - start
    assert status.status == "disconnected"
    assert duration < 3.0, f"Failure detection took {duration:.2f}s, expected < 3.0s"
