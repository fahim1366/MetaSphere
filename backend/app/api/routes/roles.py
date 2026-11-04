from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permissions
from app.models.role import AppPermission, AppRole
from app.models.user import AppUser
from app.schemas.role import PermissionRead, RoleRead

roles_router = APIRouter(prefix="/roles", tags=["Role & Permission Administration"])


@roles_router.get(
    "",
    response_model=list[RoleRead],
    status_code=status.HTTP_200_OK,
    summary="List Roles",
    description="Retrieve all configured system and custom roles. Requires ROLE_MANAGE permission.",
)
def list_roles(
    db: Session = Depends(get_db),
    _: AppUser = Depends(require_permissions("ROLE_MANAGE")),
) -> list[RoleRead]:
    stmt = select(AppRole).order_by(AppRole.name.asc())
    roles = db.execute(stmt).scalars().all()
    return [
        RoleRead(
            id=r.id,
            code=r.code,
            name=r.name,
            description=r.description,
            is_system=r.is_system,
            permissions=[p.code for p in r.permissions],
        )
        for r in roles
    ]


@roles_router.get(
    "/permissions",
    response_model=list[PermissionRead],
    status_code=status.HTTP_200_OK,
    summary="List Permissions",
    description="Retrieve all available permission capability codes. Requires ROLE_MANAGE permission.",
)
def list_permissions(
    db: Session = Depends(get_db),
    _: AppUser = Depends(require_permissions("ROLE_MANAGE")),
) -> list[PermissionRead]:
    stmt = select(AppPermission).order_by(AppPermission.module.asc(), AppPermission.code.asc())
    perms = db.execute(stmt).scalars().all()
    return [PermissionRead.model_validate(p) for p in perms]
