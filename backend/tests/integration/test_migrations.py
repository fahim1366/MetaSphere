import os

import pytest
from alembic import command
from alembic.config import Config
from app.core.config import settings
from sqlalchemy import create_engine, text

from tests.integration.test_hybrid_dev import is_port_open


@pytest.mark.integration
def test_alembic_upgrade_and_downgrade_idempotency() -> None:
    """Verify Alembic migration upgrade to head and downgrade to base are repeatable."""
    if not is_port_open(settings.POSTGRES_HOST, settings.POSTGRES_PORT):
        pytest.skip(
            f"PostgreSQL not reachable at {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}. "
            "Start containers with: docker compose -f infrastructure/docker-compose.yml up -d"
        )

    # Verify credentials and database reachability before running migrations
    try:
        probe_engine = create_engine(
            settings.sqlalchemy_database_url,
            connect_args={"connect_timeout": 1},
        )
        with probe_engine.connect():
            pass
    except Exception as exc:
        pytest.skip(f"PostgreSQL credentials/database connection rejected: {exc}")

    # Isolated migration test database
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    alembic_cfg = Config(os.path.join(backend_dir, "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))

    # Test upgrade to head
    command.upgrade(alembic_cfg, "head")

    # Verify alembic_version table exists and contains current revision
    engine = create_engine(settings.sqlalchemy_database_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        assert result == "0001_initial_baseline", (
            f"Expected version 0001_initial_baseline, got {result}"
        )

    # Test downgrade to base
    command.downgrade(alembic_cfg, "base")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        assert result is None, "Version table should have no version after downgrade to base"

    # Repeat upgrade to head to ensure re-application succeeds without errors
    command.upgrade(alembic_cfg, "head")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        assert result == "0001_initial_baseline"
