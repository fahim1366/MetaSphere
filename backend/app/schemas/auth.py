import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


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
        pwd = value.get_secret_value()
        if len(pwd) < 12:
            raise ValueError("Password must be at least 12 characters in length")
        if not re.search(r"[A-Z]", pwd):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", pwd):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", pwd):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pwd):
            raise ValueError("Password must contain at least one special character")
        return value
