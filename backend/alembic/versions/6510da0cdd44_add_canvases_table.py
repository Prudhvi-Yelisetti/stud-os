"""add canvases table

Revision ID: 6510da0cdd44
Revises: 40a47800da2d
Create Date: 2026-08-19T12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6510da0cdd44'
down_revision: Union[str, Sequence[str], None] = '40a47800da2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'canvases',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('data', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('is_trashed', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('trashed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_canvases_user_id'), 'canvases', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_canvases_user_id'), table_name='canvases')
    op.drop_table('canvases')
