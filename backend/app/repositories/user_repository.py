import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.user import AppUser, AppUserSession


def get_user_by_username(db: Session, username: str) -> AppUser | None:
    """Retrieve an active or inactive user by case-insensitive username."""
    stmt = select(AppUser).where(func.lower(AppUser.username) == username.lower())
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_email(db: Session, email: str) -> AppUser | None:
    """Retrieve user by case-insensitive email."""
    stmt = select(AppUser).where(func.lower(AppUser.email) == email.lower())
    return db.execute(stmt).scalar_one_or_none()


def get_user_by_id(db: Session, user_id: uuid.UUID) -> AppUser | None:
    """Retrieve user by UUID."""
    return db.get(AppUser, user_id)


def create_user(
    db: Session,
    username: str,
    email: str,
    password_hash: str,
    full_name: str | None = None,
    is_active: bool = True,
    is_superuser: bool = False,
) -> AppUser:
    """Create and persist a new user record."""
    user = AppUser(
        username=username,
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        is_active=is_active,
        is_superuser=is_superuser,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_session(
    db: Session,
    user_id: uuid.UUID,
    token_hash: str,
    expires_at: datetime,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AppUserSession:
    """Create and persist an active user session."""
    session = AppUserSession(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session_by_token_hash(db: Session, token_hash: str) -> AppUserSession | None:
    """Retrieve session by token hash, joined with active user."""
    stmt = select(AppUserSession).where(
        AppUserSession.token_hash == token_hash,
        AppUserSession.is_revoked.is_(False),
        AppUserSession.expires_at > func.now(),
    )
    return db.execute(stmt).scalar_one_or_none()


def touch_session(db: Session, token_hash: str, when: datetime) -> None:
    """Record session activity to support sliding idle-timeout."""
    db.execute(
        update(AppUserSession)
        .where(AppUserSession.token_hash == token_hash)
        .values(last_activity_at=when)
    )
    db.commit()


def revoke_session(db: Session, token_hash: str) -> bool:
    """Revoke a single session token."""
    stmt = (
        update(AppUserSession)
        .where(AppUserSession.token_hash == token_hash)
        .values(is_revoked=True)
    )
    result = db.execute(stmt)
    db.commit()
    count = getattr(result, "rowcount", 0)
    return bool(count and count > 0)


def revoke_all_user_sessions(db: Session, user_id: uuid.UUID) -> int:
    """Revoke all active sessions belonging to a specific user."""
    stmt = (
        update(AppUserSession)
        .where(
            AppUserSession.user_id == user_id,
            AppUserSession.is_revoked.is_(False),
        )
        .values(is_revoked=True)
    )
    result = db.execute(stmt)
    db.commit()
    return int(getattr(result, "rowcount", 0) or 0)


def record_failed_login(
    db: Session, user: AppUser, max_attempts: int, lockout_minutes: int
) -> None:
    """Increment failed login attempts and lock account if threshold is exceeded."""
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= max_attempts:
        from datetime import timedelta

        user.locked_until = datetime.now(UTC) + timedelta(minutes=lockout_minutes)
    db.commit()


def reset_failed_login(db: Session, user: AppUser) -> None:
    """Reset failed login attempts and clear lockout on successful authentication."""
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
