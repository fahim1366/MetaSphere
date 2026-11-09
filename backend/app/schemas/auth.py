import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from app.core.password_policy import validate_password_strength


class LoginRequest(BaseModel):
    """Payload for user login."""

    username: str = Field(min_length=1, max_length=50, description="Login handle")
    password: SecretStr = Field(description="Account password")


class UserRead(BaseModel):
    """Public authenticated user profile."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    email: str
    full_name: str | None = None
    is_active: bool
    is_superuser: bool
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class TokenResponse(BaseModel):
    """Authenticated session token response."""

    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user: UserRead


class ChangePasswordRequest(BaseModel):
    """Payload for password change."""

    current_password: SecretStr
    new_password: SecretStr

    @field_validator("new_password")
    @classmethod
    def validate_password_complexity(cls, value: SecretStr) -> SecretStr:
        validate_password_strength(value.get_secret_value())
        return value
