from pydantic import BaseModel, Field, SecretStr, field_validator

from app.core.password_policy import validate_password_strength


class UserCreate(BaseModel):
    """Payload to create a new user account."""

    username: str = Field(min_length=1, max_length=50)
    email: str = Field(max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: SecretStr
    full_name: str | None = Field(default=None, max_length=100)
    role_codes: list[str] = Field(default_factory=list)

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, value: SecretStr) -> SecretStr:
        validate_password_strength(value.get_secret_value())
        return value


class UserUpdate(BaseModel):
    """Payload to update an existing user."""

    email: str | None = Field(default=None, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    full_name: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None
    role_codes: list[str] | None = None
