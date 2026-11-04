import contextlib
import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

# Initialize Argon2id password hasher with configured security parameters
ph = PasswordHasher(
    time_cost=settings.ARGON2_TIME_COST,
    memory_cost=settings.ARGON2_MEMORY_COST,
    parallelism=settings.ARGON2_PARALLELISM,
    hash_len=32,
    salt_len=16,
)

# Constant pre-computed hash for dummy verification to prevent timing enumeration
DUMMY_ARGON2_HASH = ph.hash("DummyPassword123!SafeEnumerationDefense")


def hash_password(password: str) -> str:
    """Hash plaintext password using Argon2id."""
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify plaintext password against an Argon2id hash."""
    try:
        return ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def verify_dummy_password() -> None:
    """Execute constant-time dummy hash verification when username does not exist."""
    with contextlib.suppress(Exception):
        ph.verify(DUMMY_ARGON2_HASH, "DummyPasswordAttempt")


def generate_session_token() -> str:
    """Generate high-entropy (256-bit) cryptographically unguessable token."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """Compute SHA-256 hex digest of a session token for safe storage and lookups."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
