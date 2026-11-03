from datetime import UTC, datetime

from fastapi import APIRouter, Response, status

from app.core.health_probe import execute_readiness_probe
from app.schemas.health import HealthLiveResponse, HealthReadyResponse

health_router = APIRouter(prefix="/health", tags=["Health & Observability"])


@health_router.get(
    "/live",
    response_model=HealthLiveResponse,
    status_code=status.HTTP_200_OK,
    summary="Process Liveness Probe",
    description="Returns HTTP 200 if the FastAPI application process is up and running. Evaluated purely in-memory.",
)
async def check_liveness() -> HealthLiveResponse:
    """Liveness probe returning HTTP 200 without datastore inspection."""
    return HealthLiveResponse(
        status="live",
        timestamp=datetime.now(UTC),
        service="metasphere-backend",
        version="0.1.0",
    )


@health_router.get(
    "/ready",
    response_model=HealthReadyResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "All monitored dependencies are operational"},
        503: {
            "description": "One or more dependencies are unavailable",
            "model": HealthReadyResponse,
        },
    },
    summary="Dependency Readiness Probe",
    description="Validates active connectivity to PostgreSQL and Redis concurrently with bounded admission control.",
)
async def check_readiness(response: Response) -> HealthReadyResponse:
    """Readiness probe validating PostgreSQL and Redis connections."""
    health_result, http_status = await execute_readiness_probe()
    response.status_code = http_status
    return health_result
