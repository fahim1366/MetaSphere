import logging
from collections.abc import Callable, Generator
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_session_token
from app.db.session import SessionLocal
from app.models.user import AppUser
from app.repositories.user_repository import (
    get_session_by_token_hash,
    get_user_by_id,
    revoke_session,
    touch_session,
)
from app.services.rbac_service import calculate_effective_permissions

security_bearer = HTTPBearer(auto_error=False)
logger = logging.getLogger("app.auth")

# Do not write last_activity_at on every request; refresh at most once per interval.
_ACTIVITY_TOUCH_INTERVAL = timedelta(seconds=60)


def _as_utc(value: datetime) -> datetime:
    """Treat naive datetimes (e.g. from SQLite) as UTC."""
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def get_db() -> Generator[Session, None, None]:
    """Provide a managed SQLAlchemy database session per request."""
    session: Session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(security_bearer),
    db: Session = Depends(get_db),
) -> AppUser:
    """Validate Bearer session token and return the authenticated active user."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raw_token = credentials.credentials
    token_hash = hash_session_token(raw_token)

    session_record = get_session_by_token_hash(db, token_hash)
    if not session_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked session token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    now = datetime.now(UTC)
    idle_limit = timedelta(minutes=settings.SESSION_SLIDING_ACTIVITY_MINUTES)
    last_activity = _as_utc(session_record.last_activity_at)
    if now - last_activity > idle_limit:
        revoke_session(db, token_hash)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked session token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if now - last_activity > _ACTIVITY_TOUCH_INTERVAL:
        touch_session(db, token_hash, now)

    user = get_user_by_id(db, session_record.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_permissions(*required_perms: str) -> Callable[[AppUser], AppUser]:
    """Dependency factory enforcing that the authenticated user possesses all specified permissions."""

    def permission_checker(current_user: AppUser = Depends(get_current_user)) -> AppUser:
        if current_user.is_superuser:
            return current_user

        user_perms = set(calculate_effective_permissions(current_user))
        missing = [p for p in required_perms if p not in user_perms]

        if missing:
            # Log the specifics server-side; do not disclose the permission model to the client.
            logger.warning(
                "Permission denied for user=%s missing=%s", current_user.username, missing
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )

        return current_user

    return permission_checker
