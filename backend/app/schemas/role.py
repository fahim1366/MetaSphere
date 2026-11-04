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


class RoleCreate(BaseModel):
    """Payload to create a new custom governance role."""

    code: str = Field(min_length=3, max_length=50, pattern=r"^[A-Z0-9_]+$")
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None
    permission_codes: list[str] = Field(default_factory=list)


class RoleUserRead(BaseModel):
    """User assigned to a role."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    full_name: str | None = None
    email: str
    is_active: bool


class RoleRead(BaseModel):
    """Public role schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    description: str | None = None
    is_system: bool
    permissions: list[str] = Field(default_factory=list)
    assigned_user_count: int = 0
