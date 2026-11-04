from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permissions
from app.core.security import hash_password
from app.models.role import AppRole
from app.models.user import AppUser
from app.repositories.user_repository import (
    create_user,
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

    # Resolve roles
    roles: list[AppRole] = []
    if req.role_codes:
        stmt = select(AppRole).where(AppRole.code.in_(req.role_codes))
        roles = list(db.execute(stmt).scalars().all())

    pwd_hash = hash_password(req.password.get_secret_value())
    new_user = create_user(
        db=db,
        username=req.username,
        email=req.email,
        password_hash=pwd_hash,
        full_name=req.full_name,
        is_active=True,
    )
    new_user.roles = roles
    db.commit()
    db.refresh(new_user)

    log_security_event(
        db=db,
        event_type="USER_CREATED",
        status="SUCCESS",
        user_id=new_user.id,
        actor_id=current_admin.id,
        target_resource=new_user.username,
        details={"roles": [r.code for r in roles]},
    )

    return build_user_read(new_user)
