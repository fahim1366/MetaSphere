import contextvars
import logging
import re
import sys

# Context variable for request correlation ID
correlation_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)

# Regex patterns for secret masking
URI_CREDENTIAL_PATTERN = re.compile(r"(://[^:]+:)([^@]+)(@)")
KEY_VALUE_SECRET_PATTERN = re.compile(
    r"(?i)(password|secret|token|key|api_key|access_token)[=\s:]+[\"']?([^\"'\s,;]+)[\"']?"
)
BEARER_AUTH_PATTERN = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9_\-\.]+")


def mask_secrets(text: str) -> str:
    """Mask credentials, tokens, and secrets from log messages and exception tracebacks."""
    if not isinstance(text, str):
        return text

    # Mask URI credentials: postgresql://user:pass@host -> postgresql://user:***@host
    masked = URI_CREDENTIAL_PATTERN.sub(r"\1***\3", text)

    # Mask key-value secrets: password=secret123 -> password=***
    masked = KEY_VALUE_SECRET_PATTERN.sub(r"\1=***", masked)

    # Mask Bearer tokens: Bearer abc.123.xyz -> Bearer ***
    masked = BEARER_AUTH_PATTERN.sub(r"\1***", masked)

    return masked


class SecretMaskingFilter(logging.Filter):
    """Logging filter that scrubs credentials and adds correlation IDs to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Add correlation ID to record if available
        cid = correlation_id_ctx.get()
        record.correlation_id = cid or "-"

        # Mask message
        if isinstance(record.msg, str):
            record.msg = mask_secrets(record.msg)

        # Mask args if string
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: (mask_secrets(v) if isinstance(v, str) else v)
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    mask_secrets(v) if isinstance(v, str) else v for v in record.args
                )

        return True


def setup_logging(log_level: str = "INFO") -> None:
    """Configure centralized structured logging for FastAPI and Celery processes."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Format includes timestamp, severity, logger name, correlation_id, and message
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] [corr=%(correlation_id)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(SecretMaskingFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Reduce noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
