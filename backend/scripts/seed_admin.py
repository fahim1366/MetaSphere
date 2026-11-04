"""Bootstrap and seed administrative users and system roles into the MetaSphere database."""

import sys
import uuid
from pathlib import Path

# Add backend directory to sys.path so app can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.role import AppPermission, AppRole
from app.models.user import AppUser


def seed_database() -> None:
    print("[1/4] Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        print("[2/4] Seeding core system permissions...")
        permissions_data = [
            ("CATALOG_READ", "Catalog Read", "catalog", "Permission to search and view catalog metadata"),
            ("CATALOG_WRITE", "Catalog Write", "catalog", "Permission to edit business descriptions and tags"),
            ("METADATA_EXTRACT", "Metadata Extraction", "connector", "Permission to trigger metadata discovery"),
            ("USER_MANAGE", "User Administration", "admin", "Permission to manage catalog user accounts"),
            ("ROLE_MANAGE", "Role Administration", "admin", "Permission to view and manage governance roles"),
            ("AUDIT_READ", "Audit Inspection", "security", "Permission to inspect immutable security audit logs"),
        ]

        perms: dict[str, AppPermission] = {}
        for code, name, module, desc in permissions_data:
            existing = session.execute(select(AppPermission).where(AppPermission.code == code)).scalar_one_or_none()
            if not existing:
                perm = AppPermission(id=uuid.uuid4(), code=code, name=name, module=module, description=desc)
                session.add(perm)
                perms[code] = perm
            else:
                perms[code] = existing
        session.commit()

        print("[3/4] Seeding system roles...")
        roles_data = [
            ("ROLE_SUPER_ADMIN", "Super Administrator", "Full unconstrained administrative privileges", True, list(perms.values())),
            ("ROLE_ADMIN", "Administrator", "User, role, and audit management", True, [perms["USER_MANAGE"], perms["ROLE_MANAGE"], perms["CATALOG_READ"], perms["AUDIT_READ"]]),
            ("ROLE_DATA_STEWARD", "Data Steward", "Metadata curation and discovery", True, [perms["CATALOG_READ"], perms["CATALOG_WRITE"], perms["METADATA_EXTRACT"]]),
            ("ROLE_USER", "Catalog Consumer", "Search and discover catalog metadata", True, [perms["CATALOG_READ"]]),
        ]

        roles: dict[str, AppRole] = {}
        for code, name, desc, is_sys, role_perms in roles_data:
            existing_role = session.execute(select(AppRole).where(AppRole.code == code)).scalar_one_or_none()
            if not existing_role:
                r = AppRole(id=uuid.uuid4(), code=code, name=name, description=desc, is_system=is_sys, permissions=role_perms)
                session.add(r)
                roles[code] = r
            else:
                roles[code] = existing_role
        session.commit()

        print("[4/4] Seeding administrator accounts...")
        # Super Admin
        admin_user = session.execute(select(AppUser).where(AppUser.username == "admin")).scalar_one_or_none()
        if not admin_user:
            admin_user = AppUser(
                id=uuid.uuid4(),
                username="admin",
                email="admin@metasphere.local",
                full_name="System Administrator",
                password_hash=hash_password("Admin@123456"),
                is_active=True,
                is_superuser=True,
                roles=[roles["ROLE_SUPER_ADMIN"]],
            )
            session.add(admin_user)
            print("  -> Created user: admin (Password: Admin@123456)")
        else:
            print("  -> User admin already exists.")

        # Data Steward
        steward_user = session.execute(select(AppUser).where(AppUser.username == "steward")).scalar_one_or_none()
        if not steward_user:
            steward_user = AppUser(
                id=uuid.uuid4(),
                username="steward",
                email="steward@metasphere.local",
                full_name="Sarah Steward",
                password_hash=hash_password("User@123456"),
                is_active=True,
                is_superuser=False,
                roles=[roles["ROLE_DATA_STEWARD"]],
            )
            session.add(steward_user)
            print("  -> Created user: steward (Password: User@123456)")

        session.commit()
        print("\nDatabase seeding completed successfully!")
    except Exception as exc:
        session.rollback()
        print(f"ERROR: Seeding failed: {exc}", file=sys.stderr)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
