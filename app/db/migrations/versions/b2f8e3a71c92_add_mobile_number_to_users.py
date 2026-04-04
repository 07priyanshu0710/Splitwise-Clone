"""add mobile_number to users

Revision ID: b2f8e3a71c92
Revises: adfd13a16a47
Create Date: 2026-04-04 22:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2f8e3a71c92'
down_revision: Union[str, None] = 'adfd13a16a47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('mobile_number', sa.String(), nullable=True))
    op.create_index(op.f('ix_users_mobile_number'), 'users', ['mobile_number'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_mobile_number'), table_name='users')
    op.drop_column('users', 'mobile_number')
