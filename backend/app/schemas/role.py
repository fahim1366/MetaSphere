import uuid

from pydantic import BaseModel, ConfigDict, Field


class PermissionRead(BaseModel):
    """Public permission schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    module: str
    description: str | None = None


class RoleRead(BaseModel):
    """Public role schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    description: str | None = None
    is_system: bool
    permissions: list[str] = Field(default_factory=list)
