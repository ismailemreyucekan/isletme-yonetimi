"""add waiter_calls

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-30 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'waiter_calls',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('restaurant_id', sa.Uuid(), nullable=False),
        sa.Column('table_id', sa.Uuid(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'resolved', name='waitercallstatus', native_enum=False), nullable=False),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['table_id'], ['tables.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_waiter_calls_restaurant_id'), 'waiter_calls', ['restaurant_id'], unique=False)
    op.create_index(op.f('ix_waiter_calls_table_id'), 'waiter_calls', ['table_id'], unique=False)
    op.create_index(op.f('ix_waiter_calls_status'), 'waiter_calls', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_waiter_calls_status'), table_name='waiter_calls')
    op.drop_index(op.f('ix_waiter_calls_table_id'), table_name='waiter_calls')
    op.drop_index(op.f('ix_waiter_calls_restaurant_id'), table_name='waiter_calls')
    op.drop_table('waiter_calls')
