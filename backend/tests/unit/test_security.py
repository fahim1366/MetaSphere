import pytest
from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_dummy_password,
    verify_password,
)


@pytest.mark.unit
def test_argon2id_hash_and_verification() -> None:
    """Verify that Argon2id generates valid hashes and correctly validates passwords."""
    raw_password = "CorrectHorseBatteryStaple123!"
    password_hash = hash_password(raw_password)

    # Must start with $argon2id$ format identifier
    assert password_hash.startswith("$argon2id$")

    # Correct password succeeds
    assert verify_password(raw_password, password_hash) is True

    # Incorrect password fails
    assert verify_password("WrongPassword999!", password_hash) is False


@pytest.mark.unit
def test_dummy_verification_does_not_raise() -> None:
    """Verify dummy verification executes smoothly for non-existent users."""
    # Should execute in constant time and return normally
    verify_dummy_password()


@pytest.mark.unit
def test_session_token_entropy_and_hashing() -> None:
    """Verify token generation generates unique, high-entropy tokens and valid SHA-256 digests."""
    token1 = generate_session_token()
    token2 = generate_session_token()

    assert token1 != token2
    assert len(token1) >= 40  # base64 URL safe for 32 bytes is ~43 chars

    hash1 = hash_session_token(token1)
    hash2 = hash_session_token(token2)

    assert hash1 != hash2
    assert len(hash1) == 64  # SHA-256 hex digest length
