from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permissions
from app.core.security import hash_password
from app.models.role import AppRole
from app.models.user import AppUser
from app.repositories.user_repository import (
    get_user_by_email,
    get_user_by_username,
)
from app.schemas.auth import UserRead
from app.schemas.user import UserCreate
from app.services.audit_service import log_security_event
from app.services.rbac_service import build_user_read

users_router = APIRouter(prefix="/users", tags=["User Administration"])


@users_router.get(
    "",
    response_model=list[UserRead],
    status_code=status.HTTP_200_OK,
    summary="List Users",
    description="Retrieve all catalog users. Requires USER_MANAGE permission.",
)
def list_users(
    db: Session = Depends(get_db),
    _: AppUser = Depends(require_permissions("USER_MANAGE")),
) -> list[UserRead]:
    stmt = select(AppUser).order_by(AppUser.created_at.desc())
    users = db.execute(stmt).scalars().all()
    return [build_user_read(u) for u in users]


@users_router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create User",
    description="Create a new local user account with assigned roles. Requires USER_MANAGE permission.",
)
def create_new_user(
    req: UserCreate,
    db: Session = Depends(get_db),
    current_admin: AppUser = Depends(require_permissions("USER_MANAGE")),
) -> UserRead:
    if get_user_by_username(db, req.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{req.username}' is already in use",
        )
    if get_user_by_email(db, req.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{req.email}' is already in use",
        )

    # Resolve roles; reject unknown codes instead of silently ignoring them
    requested = list(dict.fromkeys(req.role_codes))
    roles: list[AppRole] = []
    if requested:
        roles = list(db.execute(select(AppRole).where(AppRole.code.in_(requested))).scalars().all())
        unknown = sorted(set(requested) - {r.code for r in roles})
        if unknown:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown role code(s): {', '.join(unknown)}",
            )

    new_user = AppUser(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password.get_secret_value()),
        full_name=req.full_name,
        is_active=True,
        roles=roles,
    )
    db.add(new_user)
    db.flush()  # assigns the primary key without committing

    log_security_event(
        db=db,
        event_type="USER_CREATED",
        status="SUCCESS",
        user_id=new_user.id,
        actor_id=current_admin.id,
        target_resource=new_user.username,
        details={"roles": [r.code for r in roles]},
        commit=False,
    )
    db.commit()  # user, role links and audit entry land together
    db.refresh(new_user)

    return build_user_read(new_user)
