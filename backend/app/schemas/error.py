from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard client-facing error schema preventing internal detail leakage."""

    detail: str = Field(description="Client-safe sanitized error message")
    correlation_id: str = Field(description="Request correlation ID matching server-side logs")
