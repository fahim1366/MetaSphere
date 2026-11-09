"""Bootstrap and seed administrative users and system roles into the MetaSphere database."""

import os
import secrets
import string
import sys
import uuid
from pathlib import Path

# Add backend directory to sys.path so app can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.core.permissions import PERMISSION_DEFINITIONS
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.role import AppPermission, AppRole
from app.models.user import AppUser
from sqlalchemy import select


def _resolve_password(env_var: str) -> tuple[str, bool]:
    """Return (password, was_generated). Prefer the environment; otherwise generate a strong one."""
    value = os.environ.get(env_var)
    if value:
        return value, False
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        candidate = "".join(secrets.choice(alphabet) for _ in range(20))
        if (
            any(c.islower() for c in candidate)
            and any(c.isupper() for c in candidate)
            and any(c.isdigit() for c in candidate)
            and any(c in "!@#$%^&*" for c in candidate)
        ):
            return candidate, True


def seed_database() -> None:
    if settings.APP_ENV == "production":
        print("[1/4] Production mode: skipping create_all (schema must come from Alembic).")
    else:
        print("[1/4] Ensuring database tables exist (development convenience)...")
        Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        print("[2/4] Seeding core system permissions...")
        permissions_data = list(PERMISSION_DEFINITIONS)

        perms: dict[str, AppPermission] = {}
        for code, name, module, desc in permissions_data:
            existing = session.execute(
                select(AppPermission).where(AppPermission.code == code)
            ).scalar_one_or_none()
            if not existing:
                perm = AppPermission(
                    id=uuid.uuid4(), code=code, name=name, module=module, description=desc
                )
                session.add(perm)
                perms[code] = perm
            else:
                perms[code] = existing
        session.commit()

        print("[3/4] Seeding system roles...")
        roles_data = [
            (
                "ROLE_SUPER_ADMIN",
                "Super Administrator",
                "Full unconstrained administrative privileges",
                True,
                list(perms.values()),
            ),
            (
                "ROLE_ADMIN",
                "Administrator",
                "User, role, and audit management",
                True,
                [
                    perms["USER_MANAGE"],
                    perms["ROLE_MANAGE"],
                    perms["CATALOG_READ"],
                    perms["AUDIT_READ"],
                ],
            ),
            (
                "ROLE_DATA_STEWARD",
                "Data Steward",
                "Metadata curation and discovery",
                True,
                [perms["CATALOG_READ"], perms["CATALOG_WRITE"], perms["METADATA_EXTRACT"]],
            ),
            (
                "ROLE_USER",
                "Catalog Consumer",
                "Search and discover catalog metadata",
                True,
                [perms["CATALOG_READ"]],
            ),
        ]

        roles: dict[str, AppRole] = {}
        for code, name, desc, is_sys, role_perms in roles_data:
            existing_role = session.execute(
                select(AppRole).where(AppRole.code == code)
            ).scalar_one_or_none()
            if not existing_role:
                r = AppRole(
                    id=uuid.uuid4(),
                    code=code,
                    name=name,
                    description=desc,
                    is_system=is_sys,
                    permissions=role_perms,
                )
                session.add(r)
                roles[code] = r
            else:
                roles[code] = existing_role
        session.commit()

        print("[4/4] Seeding administrator accounts...")
        # Super Admin
        admin_user = session.execute(
            select(AppUser).where(AppUser.username == "admin")
        ).scalar_one_or_none()
        if not admin_user:
            admin_password, admin_generated = _resolve_password("SEED_ADMIN_PASSWORD")
            admin_user = AppUser(
                id=uuid.uuid4(),
                username="admin",
                email="admin@metasphere.local",
                full_name="System Administrator",
                password_hash=hash_password(admin_password),
                is_active=True,
                is_superuser=True,
                roles=[roles["ROLE_SUPER_ADMIN"]],
            )
            session.add(admin_user)
            if admin_generated:
                print("  -> Created user: admin")
                print(f"     Generated one-time password (store it now): {admin_password}")
            else:
                print("  -> Created user: admin (password taken from SEED_ADMIN_PASSWORD)")
        else:
            print("  -> User admin already exists.")

        # Data Steward
        steward_user = session.execute(
            select(AppUser).where(AppUser.username == "steward")
        ).scalar_one_or_none()
        if not steward_user and os.environ.get("SEED_DEMO_USERS") == "1":
            steward_password, steward_generated = _resolve_password("SEED_STEWARD_PASSWORD")
            steward_user = AppUser(
                id=uuid.uuid4(),
                username="steward",
                email="steward@metasphere.local",
                full_name="Sarah Steward",
                password_hash=hash_password(steward_password),
                is_active=True,
                is_superuser=False,
                roles=[roles["ROLE_DATA_STEWARD"]],
            )
            session.add(steward_user)
            print("  -> Created demo user: steward")
            if steward_generated:
                print(f"     Generated one-time password (store it now): {steward_password}")

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
