"""add task_datetime and deadline columns to todos table

Revision ID: 71fd3b356683
Revises: 60fc2a245572
Create Date: 2026-09-22 18:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '71fd3b356683'
down_revision: Union[str, Sequence[str], None] = '60fc2a245572'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('todos', sa.Column('task_datetime', sa.DateTime(), nullable=True))
    op.add_column('todos', sa.Column('deadline', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('todos', 'deadline')
    op.drop_column('todos', 'task_datetime')
