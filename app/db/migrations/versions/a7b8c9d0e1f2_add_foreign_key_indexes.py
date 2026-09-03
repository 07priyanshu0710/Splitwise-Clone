"""add foreign key indexes

Revision ID: a7b8c9d0e1f2
Revises: d4e5f6a7b8c9
Create Date: 2026-09-03 10:55:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_expenses_payer_id",
        "expenses",
        ["payer_id"],
        unique=False,
    )
    op.create_index(
        "ix_expense_splits_user_id",
        "expense_splits",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_expense_splits_user_id", table_name="expense_splits")
    op.drop_index("ix_expenses_payer_id", table_name="expenses")
