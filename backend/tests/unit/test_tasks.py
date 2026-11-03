import uuid
from datetime import UTC, datetime

import pytest
from app.jobs.tasks import health_check_task


@pytest.mark.unit
def test_health_check_task_unit_execution() -> None:
    """Verify health_check_task runs in isolation and produces valid contract payload."""
    test_ping_id = str(uuid.uuid4())
    sent_at = datetime.now(UTC).isoformat()

    # Call underlying task function directly
    result = health_check_task.apply(args=[test_ping_id, sent_at]).get()

    assert isinstance(result, dict)
    assert result["ping_id"] == test_ping_id
    assert result["status"] == "pong"
    assert isinstance(result["worker_name"], str)
    assert len(result["worker_name"]) > 0
    assert isinstance(result["completed_at"], str)
    assert isinstance(result["duration_ms"], (int, float))
    assert result["duration_ms"] >= 0.0

    # Verify timestamp format parses as valid ISO 8601
    dt = datetime.fromisoformat(result["completed_at"])
    assert dt.tzinfo is not None, "Timestamp must be timezone-aware (UTC)"
