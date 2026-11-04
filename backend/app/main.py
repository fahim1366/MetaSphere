import logging
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.api.api_router import api_router
from app.api.routes.health import health_router
from app.core.config import settings
from app.core.exceptions import global_exception_handler
from app.core.health_probe import admission_controller
from app.core.logging import correlation_id_ctx, setup_logging
from app.db.session import engine

# Initialize structured logging with secret masking filter
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage process-scoped startup and shutdown lifecycle."""
    logger.info("Starting up %s (env=%s)...", settings.APP_NAME, settings.APP_ENV)
    yield
    logger.info("Shutting down %s...", settings.APP_NAME)
    admission_controller.shutdown()
    engine.dispose()
    logger.info("Database engine connections and health executors disposed successfully.")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Ensure every HTTP request has an X-Correlation-ID header and context variable."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        corr_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        token = correlation_id_ctx.set(corr_id)
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = corr_id
            return response
        finally:
            correlation_id_ctx.reset(token)


app = FastAPI(
    title=settings.APP_NAME,
    description="MetaSphere Enterprise Data Catalog Backend API",
    version="0.1.0",
    docs_url=f"{settings.API_V1_PREFIX}/docs" if settings.DEBUG else None,
    redoc_url=f"{settings.API_V1_PREFIX}/redoc" if settings.DEBUG else None,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Exception handlers
app.add_exception_handler(Exception, global_exception_handler)

# Middlewares
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(health_router)
