from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ComponentStatus(BaseModel):
    """Runtime status of an underlying infrastructure dependency."""

    name: str = Field(description="Component identifier, e.g., postgres, redis")
    status: Literal["connected", "disconnected", "error"] = Field(
        description="Connectivity state of the component"
    )
    latency_ms: float | None = Field(
        default=None,
        ge=0.0,
        description="Round-trip probe duration in milliseconds",
    )
    error: str | None = Field(
        default=None,
        description="Sanitized error description if probe failed (no credentials or topology)",
    )


class HealthLiveResponse(BaseModel):
    """Response payload for GET /health/live."""

    status: Literal["live"] = Field(default="live", description="Process liveness state")
    timestamp: datetime = Field(description="UTC timestamp of the probe")
    service: str = Field(default="metasphere-backend", description="Service identifier")
    version: str = Field(default="0.1.0", description="Application version")


class HealthReadyResponse(BaseModel):
    """Response payload for GET /health/ready."""

    status: Literal["ready", "unhealthy"] = Field(
        description="Overall readiness state (ready only if all components are connected)"
    )
    timestamp: datetime = Field(description="UTC timestamp of the probe")
    components: dict[str, ComponentStatus] = Field(description="Map of dependency check results")
