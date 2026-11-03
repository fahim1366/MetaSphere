import statistics
import time

import pytest
from app.core.config import settings
from app.main import app
from fastapi.testclient import TestClient

from tests.integration.test_hybrid_dev import is_port_open


@pytest.mark.benchmark
@pytest.mark.integration
def test_readiness_latency_benchmark() -> None:
    """Opt-in latency benchmark measuring P95 latency across 100 sequential readiness probes."""
    if not (
        is_port_open(settings.POSTGRES_HOST, settings.POSTGRES_PORT)
        and is_port_open(settings.REDIS_HOST, settings.REDIS_PORT)
    ):
        pytest.skip("Benchmark requires healthy live PostgreSQL and Redis services.")

    with TestClient(app) as client:
        # Pre-warm connection pools with 5 requests
        for _ in range(5):
            client.get("/health/ready")

        durations: list[float] = []
        for _ in range(100):
            t0 = time.perf_counter()
            resp = client.get("/health/ready")
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            assert resp.status_code == 200
            durations.append(elapsed_ms)

        sorted_durations = sorted(durations)
        p95 = sorted_durations[int(len(sorted_durations) * 0.95)]
        med = float(statistics.median(durations))

        print(f"\n[Readiness Benchmark] 100 samples -> Median: {med:.2f}ms, P95: {p95:.2f}ms")
        assert p95 < 50.0, f"Readiness probe P95 was {p95:.2f}ms, exceeding 50ms requirement"
