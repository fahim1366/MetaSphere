"""Case-insensitive uniqueness for username and e-mail

Revision ID: 0003_case_insensitive_identity
Revises: 0002_auth_access_control
Create Date: 2026-11-08 12:00:00.000000

Note: this fails if existing rows differ only by letter case. Resolve such duplicates first.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_case_insensitive_identity"
down_revision: str | None = "0002_auth_access_control"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_app_user_username_lower", "app_user", [sa.text("lower(username)")], unique=True
    )
    op.create_index("uq_app_user_email_lower", "app_user", [sa.text("lower(email)")], unique=True)


def downgrade() -> None:
    op.drop_index("uq_app_user_email_lower", table_name="app_user")
    op.drop_index("uq_app_user_username_lower", table_name="app_user")
