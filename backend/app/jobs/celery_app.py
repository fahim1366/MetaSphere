import logging
import socket
from typing import Any

from celery import Celery
from celery.signals import after_setup_logger, after_setup_task_logger, worker_process_init

from app.core.config import settings
from app.core.logging import SecretMaskingFilter

celery_app = Celery(
    "metasphere_jobs",
    broker=settings.effective_celery_broker_url,
    backend=settings.effective_celery_result_backend,
    include=["app.jobs.tasks"],
)

# Celery Configuration
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    broker_connection_retry_on_startup=True,
    result_expires=3600,
    broker_transport_options={
        "visibility_timeout": 3600,
        "socket_timeout": settings.REDIS_SOCKET_TIMEOUT,
        "socket_connect_timeout": settings.REDIS_CONNECT_TIMEOUT,
    },
)


@after_setup_logger.connect
@after_setup_task_logger.connect
def setup_celery_logging(logger: logging.Logger, **kwargs: Any) -> None:
    """Ensure all worker log records pass through the SecretMaskingFilter."""
    for handler in logger.handlers:
        handler.addFilter(SecretMaskingFilter())


@worker_process_init.connect
def init_worker_db_pool(**kwargs: Any) -> None:
    """Initialize process-safe database engine after worker fork with Celery pool budget."""
    from app.db.session import create_db_engine

    # Dispose inherited connections and instantiate worker-local engine
    create_db_engine(settings, role="celery")
    logging.getLogger("celery.worker").info(
        "Worker %s initialized database pool (size=%d, overflow=%d)",
        socket.gethostname(),
        settings.effective_db_pool_size,
        settings.effective_db_max_overflow,
    )
