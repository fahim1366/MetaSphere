from datetime import datetime
from unittest.mock import patch

import pytest
from app.core.health_probe import admission_controller
from app.schemas.health import ComponentStatus
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_liveness_endpoint(client: TestClient) -> None:
    """Verify /health/live returns HTTP 200, matches schema, and is in-memory only."""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "live"
    assert data["service"] == "metasphere-backend"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data
    # Parse timestamp as valid ISO
    dt = datetime.fromisoformat(data["timestamp"])
    assert dt.tzinfo is not None


@pytest.mark.unit
def test_readiness_endpoint_healthy(client: TestClient) -> None:
    """Verify /health/ready returns HTTP 200 when all dependencies report connected."""
    mock_pg = ComponentStatus(name="postgres", status="connected", latency_ms=1.2)
    mock_redis = ComponentStatus(name="redis", status="connected", latency_ms=0.8)

    with (
        patch("app.core.health_probe.probe_postgres", return_value=mock_pg),
        patch("app.core.health_probe.probe_redis", return_value=mock_redis),
    ):
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["components"]["postgres"]["status"] == "connected"
        assert data["components"]["redis"]["status"] == "connected"


@pytest.mark.unit
def test_readiness_endpoint_unhealthy_when_postgres_fails(client: TestClient) -> None:
    """Verify /health/ready returns HTTP 503 when PostgreSQL probe fails."""
    mock_pg = ComponentStatus(
        name="postgres", status="disconnected", latency_ms=2.5, error="Connection failed"
    )
    mock_redis = ComponentStatus(name="redis", status="connected", latency_ms=0.8)

    with (
        patch("app.core.health_probe.probe_postgres", return_value=mock_pg),
        patch("app.core.health_probe.probe_redis", return_value=mock_redis),
    ):
        response = client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["components"]["postgres"]["status"] == "disconnected"
        assert data["components"]["redis"]["status"] == "connected"


@pytest.mark.unit
def test_readiness_endpoint_unhealthy_when_redis_fails(client: TestClient) -> None:
    """Verify /health/ready returns HTTP 503 when Redis probe fails."""
    mock_pg = ComponentStatus(name="postgres", status="connected", latency_ms=1.2)
    mock_redis = ComponentStatus(
        name="redis", status="disconnected", latency_ms=2.0, error="Connection timeout"
    )

    with (
        patch("app.core.health_probe.probe_postgres", return_value=mock_pg),
        patch("app.core.health_probe.probe_redis", return_value=mock_redis),
    ):
        response = client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["components"]["postgres"]["status"] == "connected"
        assert data["components"]["redis"]["status"] == "disconnected"


@pytest.mark.unit
def test_readiness_admission_saturation(client: TestClient) -> None:
    """Verify exceeding max concurrent admission permits immediately returns HTTP 503."""
    with patch.object(admission_controller, "acquire_permit", return_value=False):
        response = client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["components"]["postgres"]["error"] == "Admission limit exceeded"
