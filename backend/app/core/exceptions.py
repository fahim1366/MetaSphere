import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.logging import correlation_id_ctx, mask_secrets

logger = logging.getLogger("app.exceptions")


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all unhandled exception handler ensuring no internal details leak to clients."""
    cid = correlation_id_ctx.get() or "unknown"
    sanitized_msg = mask_secrets(str(exc))

    logger.error(
        "Unhandled server error on %s %s: %s",
        request.method,
        request.url.path,
        sanitized_msg,
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "correlation_id": cid,
        },
        headers={"X-Correlation-ID": cid},
    )
