"""add_tasks_table

Revision ID: 39410db3f0e4
Revises: 6df020405d9a
Create Date: 2025-11-26 16:25:52.567776

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39410db3f0e4'
down_revision: Union[str, Sequence[str], None] = '9a033dfe52fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if tasks table exists
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'tasks' not in tables:
        # Create tasks table if it doesn't exist
        op.create_table('tasks',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('user_id', sa.Uuid(), nullable=True),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('duration_minutes', sa.Integer(), nullable=False),
            sa.Column('priority', sa.String(), nullable=False, server_default='medium'),
            sa.Column('deadline', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_tasks_created_at'), 'tasks', ['created_at'], unique=False)
    else:
        # Table exists, check and add missing columns
        columns = [col['name'] for col in inspector.get_columns('tasks')]
        
        if 'user_id' not in columns:
            op.add_column('tasks', sa.Column('user_id', sa.Uuid(), nullable=True))
            # Note: Foreign key might fail if table has data, but we'll try
            try:
                op.create_foreign_key('fk_tasks_user_id', 'tasks', 'users', ['user_id'], ['id'])
            except:
                pass  # Foreign key might already exist or fail
        
        if 'title' not in columns:
            op.add_column('tasks', sa.Column('title', sa.String(), nullable=True))
        if 'duration_minutes' not in columns:
            op.add_column('tasks', sa.Column('duration_minutes', sa.Integer(), nullable=True))
        if 'priority' not in columns:
            op.add_column('tasks', sa.Column('priority', sa.String(), nullable=True, server_default='medium'))
        if 'deadline' not in columns:
            op.add_column('tasks', sa.Column('deadline', sa.String(), nullable=True))
        if 'created_at' not in columns:
            op.add_column('tasks', sa.Column('created_at', sa.DateTime(), nullable=True))
        if 'updated_at' not in columns:
            op.add_column('tasks', sa.Column('updated_at', sa.DateTime(), nullable=True))
        
        # Create index if it doesn't exist
        indexes = [idx['name'] for idx in inspector.get_indexes('tasks')]
        if 'ix_tasks_created_at' not in indexes:
            try:
                op.create_index(op.f('ix_tasks_created_at'), 'tasks', ['created_at'], unique=False)
            except:
                pass  # Index might already exist


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_tasks_created_at'), table_name='tasks')
    op.drop_table('tasks')
