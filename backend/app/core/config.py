from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApplicationSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    APP_NAME: str = "MetaSphere Enterprise Data Catalog"
    APP_ENV: Literal["development", "test", "production"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:4200"])

    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "metasphere"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: SecretStr = SecretStr("postgres_local_dev")

    # Connection pool configuration (role-specific defaults)
    PROCESS_ROLE: Literal["api", "celery", "migration", "script"] = "api"
    DB_POOL_SIZE: int | None = None
    DB_MAX_OVERFLOW: int | None = None
    DB_POOL_TIMEOUT: float = 2.0
    DB_POOL_RECYCLE: int = 1800
    DB_CONNECT_TIMEOUT: int = 2
    DB_STATEMENT_TIMEOUT_MS: int = 2000

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_SOCKET_TIMEOUT: float = 2.0
    REDIS_CONNECT_TIMEOUT: float = 2.0

    # Celery
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def effective_db_pool_size(self) -> int:
        if self.DB_POOL_SIZE is not None:
            return self.DB_POOL_SIZE
        if self.PROCESS_ROLE == "api":
            return 10
        if self.PROCESS_ROLE == "celery":
            return 5
        return 5

    @property
    def effective_db_max_overflow(self) -> int:
        if self.DB_MAX_OVERFLOW is not None:
            return self.DB_MAX_OVERFLOW
        return 0

    @property
    def sqlalchemy_database_url(self) -> str:
        pwd = self.POSTGRES_PASSWORD.get_secret_value()
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{pwd}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def effective_celery_broker_url(self) -> str:
        return self.CELERY_BROKER_URL or self.redis_url

    @property
    def effective_celery_result_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.redis_url

    @model_validator(mode="after")
    def validate_production_settings(self) -> Self:
        if self.APP_ENV == "production":
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production environment")

            insecure_passwords = {
                "postgres",
                "postgres_local_dev",
                "password",
                "admin",
                "123456",
                "",
            }
            if self.POSTGRES_PASSWORD.get_secret_value() in insecure_passwords:
                raise ValueError("Insecure or default POSTGRES_PASSWORD rejected in production")

            for origin in self.CORS_ORIGINS:
                if "*" in origin or "localhost" in origin or "127.0.0.1" in origin:
                    raise ValueError(f"Unsafe CORS origin '{origin}' rejected in production")

        return self


settings = ApplicationSettings()
