from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import ApplicationSettings, settings


def get_engine_args(app_settings: ApplicationSettings, role: str | None = None) -> dict[str, Any]:
    """Calculate process-safe engine configuration parameters."""
    effective_role = role or app_settings.PROCESS_ROLE
    pool_size = app_settings.DB_POOL_SIZE
    if pool_size is None:
        pool_size = 10 if effective_role == "api" else 5

    max_overflow = app_settings.DB_MAX_OVERFLOW
    if max_overflow is None:
        max_overflow = 0

    return {
        "poolclass": QueuePool,
        "pool_size": pool_size,
        "max_overflow": max_overflow,
        "pool_timeout": app_settings.DB_POOL_TIMEOUT,
        "pool_recycle": app_settings.DB_POOL_RECYCLE,
        "pool_pre_ping": True,
        "connect_args": {
            "connect_timeout": app_settings.DB_CONNECT_TIMEOUT,
            "options": f"-c statement_timeout={app_settings.DB_STATEMENT_TIMEOUT_MS}",
        },
        "echo": False,
    }


def create_db_engine(
    app_settings: ApplicationSettings | None = None, role: str | None = None
) -> Engine:
    """Create a synchronous SQLAlchemy 2.x engine with role-specific pool budgeting."""
    cfg = app_settings or settings
    engine_kwargs = get_engine_args(cfg, role=role)
    return create_engine(cfg.sqlalchemy_database_url, **engine_kwargs)


# Module-level default engine for application runtime
engine: Engine = create_db_engine(settings)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
