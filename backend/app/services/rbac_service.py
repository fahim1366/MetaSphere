from app.core.permissions import ALL_PERMISSION_CODES
from app.models.user import AppUser
from app.schemas.auth import UserRead


def get_user_role_codes(user: AppUser) -> list[str]:
    """Extract list of role codes assigned to a user."""
    return [role.code for role in user.roles]


def calculate_effective_permissions(user: AppUser) -> list[str]:
    """Calculate the union of all permissions granted across all assigned roles.

    Superusers implicitly receive all permissions.
    """
    if user.is_superuser:
        return list(ALL_PERMISSION_CODES)

    permissions_set: set[str] = set()
    for role in user.roles:
        for perm in role.permissions:
            permissions_set.add(perm.code)

    return sorted(permissions_set)


def build_user_read(user: AppUser) -> UserRead:
    """Build a typed UserRead DTO with aggregated roles and effective permissions."""
    return UserRead(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        roles=get_user_role_codes(user),
        permissions=calculate_effective_permissions(user),
    )


def has_category_permission(
    user: AppUser,
    target_lineage_path: str,
    permission_code: str,
    active_grants: list[tuple[str, str]],
) -> bool:
    """Evaluate hierarchical category permission with parent-to-descendant inheritance.

    active_grants: list of (grant_lineage_path, permission_code)
    """
    if user.is_superuser:
        return True

    for grant_path, grant_perm in active_grants:
        if grant_perm == permission_code:
            # Normalized prefix check for lineage inheritance
            norm_grant = grant_path.rstrip("/") + "/"
            norm_target = target_lineage_path.rstrip("/") + "/"
            if norm_target.startswith(norm_grant) or norm_grant == "/":
                return True

    return False
