"""add_scheduled_tasks_table

Revision ID: eecfe7d19d97
Revises: 39410db3f0e4
Create Date: 2025-11-26 16:38:17.198159

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eecfe7d19d97'
down_revision: Union[str, Sequence[str], None] = '39410db3f0e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create scheduled_tasks table
    op.create_table('scheduled_tasks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('task_name', sa.String(), nullable=False),
        sa.Column('estimated_duration_minutes', sa.Integer(), nullable=False),
        sa.Column('assigned_date', sa.String(), nullable=False),
        sa.Column('assigned_start_time', sa.String(), nullable=False),
        sa.Column('assigned_end_time', sa.String(), nullable=False),
        sa.Column('slot_id', sa.String(), nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scheduled_tasks_created_at'), 'scheduled_tasks', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_scheduled_tasks_created_at'), table_name='scheduled_tasks')
    op.drop_table('scheduled_tasks')
