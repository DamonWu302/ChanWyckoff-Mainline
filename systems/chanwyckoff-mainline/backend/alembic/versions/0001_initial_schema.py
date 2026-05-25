"""initial schema baseline

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-25
"""

from collections.abc import Sequence

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

