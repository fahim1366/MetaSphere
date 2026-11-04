from pydantic import BaseModel, Field, SecretStr


class UserCreate(BaseModel):
    """Payload to create a new user account."""

    username: str = Field(min_length=1, max_length=50)
    email: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")
    password: SecretStr
    full_name: str | None = None
    role_codes: list[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    """Payload to update an existing user."""

    email: str | None = None
    full_name: str | None = None
    is_active: bool | None = None
    role_codes: list[str] | None = None
