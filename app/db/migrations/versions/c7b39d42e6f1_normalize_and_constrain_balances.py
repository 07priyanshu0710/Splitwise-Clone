"""normalize and constrain balances

Revision ID: c7b39d42e6f1
Revises: b2f8e3a71c92
Create Date: 2026-09-02 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "c7b39d42e6f1"
down_revision: Union[str, None] = "b2f8e3a71c92"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Repair any duplicate or opposing rows produced by the former
    # read-modify-write implementation before enforcing uniqueness.
    op.execute(
        """
        CREATE TEMPORARY TABLE normalized_balances ON COMMIT DROP AS
        SELECT
            LEAST(user_id, owes_to_id) AS first_user_id,
            GREATEST(user_id, owes_to_id) AS second_user_id,
            group_id,
            currency_code,
            SUM(
                CASE
                    WHEN user_id < owes_to_id THEN amount
                    ELSE -amount
                END
            ) AS net_amount
        FROM balances
        WHERE user_id <> owes_to_id AND amount > 0
        GROUP BY
            LEAST(user_id, owes_to_id),
            GREATEST(user_id, owes_to_id),
            group_id,
            currency_code
        """
    )
    op.execute("DELETE FROM balances")
    op.execute(
        """
        INSERT INTO balances (
            user_id,
            owes_to_id,
            group_id,
            amount,
            currency_code,
            last_updated
        )
        SELECT
            CASE WHEN net_amount > 0 THEN first_user_id ELSE second_user_id END,
            CASE WHEN net_amount > 0 THEN second_user_id ELSE first_user_id END,
            group_id,
            ABS(net_amount),
            currency_code,
            now()
        FROM normalized_balances
        WHERE net_amount <> 0
        """
    )

    op.create_check_constraint(
        op.f("ck_balances_different_users"),
        "balances",
        "user_id <> owes_to_id",
    )
    op.create_check_constraint(
        op.f("ck_balances_positive_amount"),
        "balances",
        "amount > 0",
    )
    op.create_index(
        "uq_balances_user_owes_group_currency",
        "balances",
        ["user_id", "owes_to_id", "group_id", "currency_code"],
        unique=True,
        postgresql_nulls_not_distinct=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_balances_user_owes_group_currency",
        table_name="balances",
    )
    op.drop_constraint(
        op.f("ck_balances_positive_amount"),
        "balances",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_balances_different_users"),
        "balances",
        type_="check",
    )
