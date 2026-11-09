import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.logging import mask_secrets
from app.models.audit import AppSecurityAudit


def sanitize_audit_details(details: dict[str, Any] | None) -> dict[str, Any] | None:
    """Recursively scrub passwords, tokens, and secret strings from audit metadata."""
    if not details:
        return None

    sanitized: dict[str, Any] = {}
    for k, v in details.items():
        if isinstance(v, str):
            sanitized[k] = mask_secrets(v)
        elif isinstance(v, dict):
            sanitized[k] = sanitize_audit_details(v)
        else:
            sanitized[k] = v
    return sanitized


def log_security_event(
    db: Session,
    event_type: str,
    status: str,
    user_id: uuid.UUID | None = None,
    actor_id: uuid.UUID | None = None,
    target_resource: str | None = None,
    ip_address: str | None = None,
    details: dict[str, Any] | None = None,
    commit: bool = True,
) -> AppSecurityAudit:
    """Record an immutable security audit event.

    With ``commit=False`` the entry joins the caller's transaction so that a business change
    and its audit record are persisted (or rolled back) atomically.
    """
    safe_details = sanitize_audit_details(details)

    audit_entry = AppSecurityAudit(
        event_type=event_type,
        status=status,
        user_id=user_id,
        actor_id=actor_id,
        target_resource=target_resource,
        ip_address=ip_address,
        details=safe_details,
    )
    db.add(audit_entry)
    if commit:
        db.commit()
        db.refresh(audit_entry)
    else:
        db.flush()
    return audit_entry
