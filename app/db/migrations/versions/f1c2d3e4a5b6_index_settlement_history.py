"""index settlement history

Revision ID: f1c2d3e4a5b6
Revises: e8a3f4c9d201
Create Date: 2026-09-02 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "f1c2d3e4a5b6"
down_revision: Union[str, None] = "e8a3f4c9d201"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_settlements_group_created_at",
        "settlements",
        ["group_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_settlements_group_created_at", table_name="settlements")
