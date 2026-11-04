import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    """Public security audit event schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    user_id: uuid.UUID | None = None
    actor_id: uuid.UUID | None = None
    target_resource: str | None = None
    status: str
    ip_address: str | None = None
    timestamp: datetime
    details: dict[str, Any] | None = None
