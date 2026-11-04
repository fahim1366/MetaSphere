from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permissions
from app.models.audit import AppSecurityAudit
from app.models.user import AppUser
from app.schemas.audit import AuditLogRead

audit_router = APIRouter(prefix="/audit", tags=["Security & Governance Audit"])


@audit_router.get(
    "/security",
    response_model=list[AuditLogRead],
    status_code=status.HTTP_200_OK,
    summary="Query Security Audit Trail",
    description="Retrieve immutable security and access audit logs. Requires AUDIT_READ permission.",
)
def get_security_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: AppUser = Depends(require_permissions("AUDIT_READ")),
) -> list[AuditLogRead]:
    stmt = (
        select(AppSecurityAudit)
        .order_by(AppSecurityAudit.timestamp.desc())
        .offset(offset)
        .limit(limit)
    )
    logs = db.execute(stmt).scalars().all()
    return [AuditLogRead.model_validate(log) for log in logs]
