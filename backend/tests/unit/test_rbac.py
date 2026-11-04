import uuid

import pytest
from app.models.role import AppPermission, AppRole
from app.models.user import AppUser
from app.services.rbac_service import calculate_effective_permissions, get_user_role_codes


@pytest.mark.unit
def test_user_with_no_roles_has_no_permissions() -> None:
    """Verify that a user without assigned roles possesses zero permissions (deny by default)."""
    user = AppUser(
        id=uuid.uuid4(),
        username="guest_user",
        email="guest@example.com",
        password_hash="fakehash",
        roles=[],
    )
    perms = calculate_effective_permissions(user)
    assert perms == []
    assert get_user_role_codes(user) == []


@pytest.mark.unit
def test_multi_role_permission_union() -> None:
    """Verify that assigning multiple roles aggregates the union of permissions."""
    perm_read = AppPermission(id=uuid.uuid4(), code="CATALOG_READ", name="Read", module="catalog")
    perm_write = AppPermission(
        id=uuid.uuid4(), code="CATALOG_WRITE", name="Write", module="catalog"
    )
    perm_audit = AppPermission(id=uuid.uuid4(), code="AUDIT_READ", name="Audit", module="audit")

    role_steward = AppRole(
        id=uuid.uuid4(),
        code="ROLE_DATA_STEWARD",
        name="Data Steward",
        permissions=[perm_read, perm_write],
    )
    role_auditor = AppRole(
        id=uuid.uuid4(),
        code="ROLE_AUDITOR",
        name="Auditor",
        permissions=[perm_read, perm_audit],
    )

    user = AppUser(
        id=uuid.uuid4(),
        username="lead_steward",
        email="lead@example.com",
        password_hash="fakehash",
        roles=[role_steward, role_auditor],
    )

    perms = calculate_effective_permissions(user)
    assert sorted(perms) == ["AUDIT_READ", "CATALOG_READ", "CATALOG_WRITE"]
    assert sorted(get_user_role_codes(user)) == ["ROLE_AUDITOR", "ROLE_DATA_STEWARD"]


@pytest.mark.unit
def test_superuser_implicitly_receives_all_permissions() -> None:
    """Verify superuser bypass flag grants all system capabilities."""
    user = AppUser(
        id=uuid.uuid4(),
        username="superadmin",
        email="super@example.com",
        password_hash="fakehash",
        is_superuser=True,
        roles=[],
    )
    perms = calculate_effective_permissions(user)
    assert "USER_MANAGE" in perms
    assert "CATALOG_READ" in perms
    assert "AUDIT_READ" in perms


@pytest.mark.unit
def test_category_permission_parent_inheritance() -> None:
    """Verify that granting a permission on a parent category automatically inherits to descendants."""
    from app.services.rbac_service import has_category_permission

    user = AppUser(
        id=uuid.uuid4(),
        username="finance_user",
        email="fin@example.com",
        password_hash="fakehash",
        roles=[],
    )

    # User has grant on /finance/
    grants = [("/finance", "CATALOG_READ")]

    # Direct child category inherits permission
    assert has_category_permission(user, "/finance/treasury", "CATALOG_READ", grants) is True
    # Grandchild category inherits permission
    assert (
        has_category_permission(user, "/finance/treasury/cash_flow", "CATALOG_READ", grants) is True
    )
    # Different category is not granted
    assert has_category_permission(user, "/engineering/devops", "CATALOG_READ", grants) is False
    # Different permission on child is not granted
    assert has_category_permission(user, "/finance/treasury", "CATALOG_WRITE", grants) is False
