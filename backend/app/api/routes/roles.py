import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permissions
from app.models.role import AppPermission, AppRole, AppUserRole
from app.models.user import AppUser
from app.schemas.role import PermissionRead, RoleCreate, RoleRead, RoleUserRead
from app.services.audit_service import log_security_event

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
    count_rows = db.execute(
        select(AppUserRole.role_id, func.count()).group_by(AppUserRole.role_id)
    ).all()
    counts = {row[0]: int(row[1]) for row in count_rows}
    return [
        RoleRead(
            id=r.id,
            code=r.code,
            name=r.name,
            description=r.description,
            is_system=r.is_system,
            permissions=[p.code for p in r.permissions],
            assigned_user_count=counts.get(r.id, 0),
        )
        for r in roles
    ]


@roles_router.post(
    "",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create Role",
    description="Create a new custom governance role with assigned permissions. Requires ROLE_MANAGE permission.",
)
def create_role(
    req: RoleCreate,
    db: Session = Depends(get_db),
    current_admin: AppUser = Depends(require_permissions("ROLE_MANAGE")),
) -> RoleRead:
    # Check if role code already exists
    existing = db.execute(select(AppRole).where(AppRole.code == req.code)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role with code '{req.code}' already exists",
        )

    # Fetch permissions
    requested = list(dict.fromkeys(req.permission_codes))
    perms: list[AppPermission] = []
    if requested:
        stmt = select(AppPermission).where(AppPermission.code.in_(requested))
        perms = list(db.execute(stmt).scalars().all())
        unknown = sorted(set(requested) - {p.code for p in perms})
        if unknown:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown permission code(s): {', '.join(unknown)}",
            )

    new_role = AppRole(
        id=uuid.uuid4(),
        code=req.code,
        name=req.name,
        description=req.description,
        is_system=False,
        permissions=perms,
    )
    db.add(new_role)
    db.flush()

    log_security_event(
        db=db,
        event_type="ROLE_CREATED",
        status="SUCCESS",
        actor_id=current_admin.id,
        target_resource=new_role.code,
        details={"permissions": [p.code for p in perms]},
        commit=False,
    )
    db.commit()
    db.refresh(new_role)

    return RoleRead(
        id=new_role.id,
        code=new_role.code,
        name=new_role.name,
        description=new_role.description,
        is_system=new_role.is_system,
        permissions=[p.code for p in new_role.permissions],
        assigned_user_count=0,
    )


@roles_router.get(
    "/{role_id}/users",
    response_model=list[RoleUserRead],
    status_code=status.HTTP_200_OK,
    summary="List Users Assigned to Role",
    description="Retrieve the list of users assigned to a specific role. Requires ROLE_MANAGE permission.",
)
def get_role_users(
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: AppUser = Depends(require_permissions("ROLE_MANAGE")),
) -> list[RoleUserRead]:
    role = db.execute(select(AppRole).where(AppRole.id == role_id)).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return [RoleUserRead.model_validate(u) for u in role.users]


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
