"""add chapter template flags

Revision ID: 40a47800da2d
Revises: 8efd67ebff84
Create Date: 2026-08-16 06:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40a47800da2d'
down_revision: Union[str, Sequence[str], None] = '8efd67ebff84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('chapters', sa.Column('is_template', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('chapters', sa.Column('is_daily_template', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column('chapters', 'is_daily_template')
    op.drop_column('chapters', 'is_template')
