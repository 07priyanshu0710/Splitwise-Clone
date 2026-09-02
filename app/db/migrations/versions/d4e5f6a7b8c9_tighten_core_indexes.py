"""tighten core indexes and group membership integrity

Revision ID: d4e5f6a7b8c9
Revises: f1c2d3e4a5b6
Create Date: 2026-09-02 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "f1c2d3e4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


REDUNDANT_PRIMARY_KEY_INDEXES = (
    ("ix_audit_logs_id", "audit_logs"),
    ("ix_users_id", "users"),
    ("ix_groups_id", "groups"),
    ("ix_balances_id", "balances"),
    ("ix_expenses_id", "expenses"),
    ("ix_group_members_id", "group_members"),
    ("ix_settlements_id", "settlements"),
    ("ix_expense_splits_id", "expense_splits"),
)

UNUSED_INDEXES = (
    ("ix_audit_logs_action", "audit_logs"),
    ("ix_audit_logs_entity_type", "audit_logs"),
    ("ix_users_full_name", "users"),
    ("ix_groups_name", "groups"),
)


def upgrade() -> None:
    for index_name, table_name in REDUNDANT_PRIMARY_KEY_INDEXES:
        op.drop_index(index_name, table_name=table_name)
    for index_name, table_name in UNUSED_INDEXES:
        op.drop_index(index_name, table_name=table_name)

    op.alter_column(
        "expenses",
        "curvature_code",
        new_column_name="currency_code",
    )

    # Retain the earliest membership if an older deployment allowed duplicates.
    op.execute(
        """
        DELETE FROM group_members duplicate
        USING group_members original
        WHERE duplicate.group_id = original.group_id
          AND duplicate.user_id = original.user_id
          AND duplicate.id > original.id
        """
    )
    op.create_unique_constraint(
        "uq_group_members_group_user",
        "group_members",
        ["group_id", "user_id"],
    )
    op.create_index(
        "ix_group_members_user_id",
        "group_members",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_expenses_group_created_at",
        "expenses",
        ["group_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_expense_splits_expense_id",
        "expense_splits",
        ["expense_id"],
        unique=False,
    )
    op.create_index(
        "ix_balances_group_id",
        "balances",
        ["group_id"],
        unique=False,
    )
    op.create_index(
        "ix_balances_owes_to_id",
        "balances",
        ["owes_to_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_balances_owes_to_id", table_name="balances")
    op.drop_index("ix_balances_group_id", table_name="balances")
    op.drop_index("ix_expense_splits_expense_id", table_name="expense_splits")
    op.drop_index("ix_expenses_group_created_at", table_name="expenses")
    op.drop_index("ix_group_members_user_id", table_name="group_members")
    op.drop_constraint(
        "uq_group_members_group_user",
        "group_members",
        type_="unique",
    )

    op.alter_column(
        "expenses",
        "currency_code",
        new_column_name="curvature_code",
    )

    for index_name, table_name in UNUSED_INDEXES:
        column_name = index_name.removeprefix(f"ix_{table_name}_")
        op.create_index(index_name, table_name, [column_name], unique=False)

    for index_name, table_name in REDUNDANT_PRIMARY_KEY_INDEXES:
        op.create_index(index_name, table_name, ["id"], unique=False)
