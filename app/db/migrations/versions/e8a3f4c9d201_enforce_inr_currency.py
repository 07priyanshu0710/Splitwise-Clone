"""enforce INR as the only currency

Revision ID: e8a3f4c9d201
Revises: c7b39d42e6f1
Create Date: 2026-09-02 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e8a3f4c9d201"
down_revision: Union[str, None] = "c7b39d42e6f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(
        "uq_balances_user_owes_group_currency",
        table_name="balances",
    )

    # Existing amounts were entered as rupees but labeled USD. Consolidate any
    # historical currency variants before enforcing the single INR invariant.
    op.execute(
        """
        CREATE TEMPORARY TABLE inr_balances ON COMMIT DROP AS
        SELECT
            LEAST(user_id, owes_to_id) AS first_user_id,
            GREATEST(user_id, owes_to_id) AS second_user_id,
            group_id,
            SUM(
                CASE
                    WHEN user_id < owes_to_id THEN amount
                    ELSE -amount
                END
            ) AS net_amount,
            MAX(last_updated) AS last_updated
        FROM balances
        WHERE user_id <> owes_to_id AND amount > 0
        GROUP BY
            LEAST(user_id, owes_to_id),
            GREATEST(user_id, owes_to_id),
            group_id
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
            'INR',
            last_updated
        FROM inr_balances
        WHERE net_amount <> 0
        """
    )

    op.execute("UPDATE expenses SET curvature_code = 'INR'")
    op.execute("UPDATE settlements SET currency_code = 'INR'")

    op.alter_column(
        "expenses",
        "curvature_code",
        existing_type=sa.String(),
        type_=sa.String(length=3),
        server_default=sa.text("'INR'"),
        existing_nullable=False,
    )
    op.alter_column(
        "settlements",
        "currency_code",
        existing_type=sa.String(),
        type_=sa.String(length=3),
        server_default=sa.text("'INR'"),
        existing_nullable=False,
    )
    op.alter_column(
        "balances",
        "currency_code",
        existing_type=sa.String(),
        type_=sa.String(length=3),
        server_default=sa.text("'INR'"),
        existing_nullable=False,
    )

    op.create_check_constraint(
        op.f("ck_expenses_currency_inr"),
        "expenses",
        "curvature_code = 'INR'",
    )
    op.create_check_constraint(
        op.f("ck_settlements_currency_inr"),
        "settlements",
        "currency_code = 'INR'",
    )
    op.create_check_constraint(
        op.f("ck_balances_currency_inr"),
        "balances",
        "currency_code = 'INR'",
    )
    op.create_index(
        "uq_balances_user_owes_group",
        "balances",
        ["user_id", "owes_to_id", "group_id"],
        unique=True,
        postgresql_nulls_not_distinct=True,
    )
def downgrade() -> None:
    op.drop_index("uq_balances_user_owes_group", table_name="balances")
    op.drop_constraint(
        op.f("ck_balances_currency_inr"),
        "balances",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_settlements_currency_inr"),
        "settlements",
        type_="check",
    )
    op.drop_constraint(
        op.f("ck_expenses_currency_inr"),
        "expenses",
        type_="check",
    )

    op.execute("UPDATE balances SET currency_code = 'USD'")
    op.execute("UPDATE settlements SET currency_code = 'USD'")
    op.execute("UPDATE expenses SET curvature_code = 'USD'")

    for table_name, column_name in (
        ("balances", "currency_code"),
        ("settlements", "currency_code"),
        ("expenses", "curvature_code"),
    ):
        op.alter_column(
            table_name,
            column_name,
            existing_type=sa.String(length=3),
            type_=sa.String(),
            server_default=None,
            existing_nullable=False,
        )

    op.create_index(
        "uq_balances_user_owes_group_currency",
        "balances",
        ["user_id", "owes_to_id", "group_id", "currency_code"],
        unique=True,
        postgresql_nulls_not_distinct=True,
    )
