from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import (
    clear_failed_login_attempts,
    is_login_rate_limited,
    record_failed_login_attempt,
)
from app.core.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_dummy_password,
    verify_password,
)
from app.models.user import AppUser
from app.repositories.user_repository import (
    create_session,
    get_session_by_token_hash,
    get_user_by_username,
    record_failed_login,
    reset_failed_login,
    revoke_all_user_sessions,
    revoke_session,
)
from app.schemas.auth import TokenResponse
from app.services.audit_service import log_security_event
from app.services.rbac_service import build_user_read


def authenticate_user(
    db: Session,
    username: str,
    password: str,
    client_ip: str | None = None,
    user_agent: str | None = None,
) -> TokenResponse:
    """Authenticate local username and password, enforcing constant-time failure and rate-limits."""
    # Check rate limiting
    rate_limit_id = client_ip or username
    if is_login_rate_limited(rate_limit_id):
        log_security_event(
            db,
            event_type="LOGIN_FAILED",
            status="BLOCKED",
            target_resource=username,
            ip_address=client_ip,
            details={"reason": "Rate limit / lockout active"},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please try again later.",
        )

    user = get_user_by_username(db, username)

    # If user does not exist, run dummy verification to maintain constant timing
    if user is None:
        verify_dummy_password()
        record_failed_login_attempt(rate_limit_id)
        log_security_event(
            db,
            event_type="LOGIN_FAILED",
            status="FAILURE",
            target_resource=username,
            ip_address=client_ip,
            details={"reason": "User not found (generic error)"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Check if account is locked
    now_utc = datetime.now(UTC)
    if user.locked_until and user.locked_until > now_utc:
        log_security_event(
            db,
            event_type="LOGIN_FAILED",
            status="BLOCKED",
            user_id=user.id,
            target_resource=username,
            ip_address=client_ip,
            details={"locked_until": user.locked_until.isoformat()},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked. Please try again later.",
        )

    # Check if account is active
    if not user.is_active:
        verify_dummy_password()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Verify password hash
    if not verify_password(password, user.password_hash):
        record_failed_login(
            db,
            user,
            max_attempts=settings.AUTH_MAX_FAILED_ATTEMPTS,
            lockout_minutes=settings.AUTH_LOCKOUT_MINUTES,
        )
        record_failed_login_attempt(rate_limit_id)
        log_security_event(
            db,
            event_type="LOGIN_FAILED",
            status="FAILURE",
            user_id=user.id,
            target_resource=username,
            ip_address=client_ip,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Success: reset failed attempts
    reset_failed_login(db, user)
    clear_failed_login_attempts(rate_limit_id)

    # Generate session token
    raw_token = generate_session_token()
    token_hash = hash_session_token(raw_token)
    expires_at = now_utc + timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)

    create_session(
        db,
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    log_security_event(
        db,
        event_type="LOGIN_SUCCESS",
        status="SUCCESS",
        user_id=user.id,
        ip_address=client_ip,
    )

    return TokenResponse(
        access_token=raw_token,
        token_type="bearer",
        expires_at=expires_at,
        user=build_user_read(user),
    )


def logout_user(db: Session, token: str, client_ip: str | None = None) -> None:
    """Invalidate active session token."""
    token_hash = hash_session_token(token)
    session = get_session_by_token_hash(db, token_hash)
    if session:
        user_id = session.user_id
        revoke_session(db, token_hash)
        log_security_event(
            db,
            event_type="LOGOUT",
            status="SUCCESS",
            user_id=user_id,
            ip_address=client_ip,
        )


def change_user_password(
    db: Session,
    user: AppUser,
    current_password: str,
    new_password: str,
    client_ip: str | None = None,
) -> None:
    """Change user password and immediately revoke all existing active sessions."""
    if not verify_password(current_password, user.password_hash):
        log_security_event(
            db,
            event_type="PASSWORD_CHANGE",
            status="FAILURE",
            user_id=user.id,
            ip_address=client_ip,
            details={"reason": "Incorrect current password"},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    # Update hash
    user.password_hash = hash_password(new_password)
    db.commit()

    # Revoke all active sessions
    revoked_count = revoke_all_user_sessions(db, user.id)

    log_security_event(
        db,
        event_type="PASSWORD_CHANGE",
        status="SUCCESS",
        user_id=user.id,
        ip_address=client_ip,
        details={"revoked_sessions": revoked_count},
    )
