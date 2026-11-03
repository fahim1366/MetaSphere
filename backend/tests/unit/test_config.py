import pytest
from app.core.config import ApplicationSettings
from pydantic import SecretStr, ValidationError


@pytest.mark.unit
def test_valid_development_settings() -> None:
    """Verify default development configuration is accepted."""
    cfg = ApplicationSettings(APP_ENV="development", DEBUG=True)
    assert cfg.APP_ENV == "development"
    assert cfg.DEBUG is True
    assert cfg.POSTGRES_PORT == 5432
    assert cfg.effective_db_pool_size == 10
    assert cfg.effective_db_max_overflow == 0


@pytest.mark.unit
def test_role_specific_pool_sizes() -> None:
    """Verify API and Celery roles receive distinct connection pool budgets."""
    api_cfg = ApplicationSettings(PROCESS_ROLE="api")
    celery_cfg = ApplicationSettings(PROCESS_ROLE="celery")

    assert api_cfg.effective_db_pool_size == 10
    assert api_cfg.effective_db_max_overflow == 0
    assert celery_cfg.effective_db_pool_size == 5
    assert celery_cfg.effective_db_max_overflow == 0


@pytest.mark.unit
def test_production_rejects_debug_true() -> None:
    """Verify production environment rejects DEBUG=True."""
    with pytest.raises(ValidationError, match="DEBUG must be False in production"):
        ApplicationSettings(
            APP_ENV="production",
            DEBUG=True,
            POSTGRES_PASSWORD=SecretStr("super_secure_prod_password_999"),
            CORS_ORIGINS=["https://catalog.enterprise.org"],
        )


@pytest.mark.unit
def test_production_rejects_default_insecure_passwords() -> None:
    """Verify production environment rejects known insecure/default passwords."""
    for insecure in ["postgres", "password", "admin", "123456", "postgres_local_dev", ""]:
        with pytest.raises(ValidationError, match="Insecure or default POSTGRES_PASSWORD"):
            ApplicationSettings(
                APP_ENV="production",
                DEBUG=False,
                POSTGRES_PASSWORD=SecretStr(insecure),
                CORS_ORIGINS=["https://catalog.enterprise.org"],
            )


@pytest.mark.unit
def test_production_rejects_unsafe_cors() -> None:
    """Verify production environment rejects wildcard and localhost CORS origins."""
    for unsafe_origin in ["*", "http://localhost:4200", "http://127.0.0.1:8000"]:
        with pytest.raises(ValidationError, match="Unsafe CORS origin"):
            ApplicationSettings(
                APP_ENV="production",
                DEBUG=False,
                POSTGRES_PASSWORD=SecretStr("secure_prod_pwd_12345"),
                CORS_ORIGINS=[unsafe_origin],
            )
