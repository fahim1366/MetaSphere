import logging

import pytest
from app.core.logging import SecretMaskingFilter, mask_secrets


@pytest.mark.unit
def test_mask_secrets_uri_credentials() -> None:
    """Verify passwords inside connection URIs are masked."""
    uri = "postgresql+psycopg2://admin:supersecret123@db.prod.internal:5432/catalog"
    masked = mask_secrets(uri)
    assert "supersecret123" not in masked
    assert masked == "postgresql+psycopg2://admin:***@db.prod.internal:5432/catalog"


@pytest.mark.unit
def test_mask_secrets_key_value() -> None:
    """Verify password, token, and secret key-values are masked."""
    log_msg = "Attempting login with password=my_secret_password and token='xyz123token'"
    masked = mask_secrets(log_msg)
    assert "my_secret_password" not in masked
    assert "xyz123token" not in masked
    assert "password=***" in masked
    assert "token=***" in masked


@pytest.mark.unit
def test_mask_secrets_bearer_auth() -> None:
    """Verify Bearer tokens are masked."""
    header_val = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    masked = mask_secrets(header_val)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in masked
    assert "Bearer ***" in masked


@pytest.mark.unit
def test_secret_masking_filter_record() -> None:
    """Verify SecretMaskingFilter masks log record messages and args."""
    filter_ = SecretMaskingFilter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Database connect failed: postgresql://user:secretpass@localhost/db",
        args=(),
        exc_info=None,
    )
    filter_.filter(record)
    assert "secretpass" not in record.msg
    assert "user:***@localhost" in record.msg
