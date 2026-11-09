"""Canonical catalogue of platform permissions (single source of truth).

Used by RBAC evaluation (superuser grant) and by the database seed script.
"""

# (code, display name, module, description)
PERMISSION_DEFINITIONS: tuple[tuple[str, str, str, str], ...] = (
    ("CATALOG_READ", "Catalog Read", "catalog", "Permission to search and view catalog metadata"),
    (
        "CATALOG_WRITE",
        "Catalog Write",
        "catalog",
        "Permission to edit business descriptions and tags",
    ),
    (
        "METADATA_EXTRACT",
        "Metadata Extraction",
        "connector",
        "Permission to trigger metadata discovery",
    ),
    (
        "SOURCE_MANAGE",
        "Data Source Management",
        "connector",
        "Permission to register, test and edit data source connections",
    ),
    ("USER_MANAGE", "User Administration", "admin", "Permission to manage catalog user accounts"),
    (
        "ROLE_MANAGE",
        "Role Administration",
        "admin",
        "Permission to view and manage governance roles",
    ),
    (
        "AUDIT_READ",
        "Audit Inspection",
        "security",
        "Permission to inspect immutable security audit logs",
    ),
)

ALL_PERMISSION_CODES: tuple[str, ...] = tuple(p[0] for p in PERMISSION_DEFINITIONS)
