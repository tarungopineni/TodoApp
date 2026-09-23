"""add_mail_sent_to_todos

Revision ID: cc3eb5910883
Revises: 71fd3b356683
Create Date: 2026-09-23 14:39:57.517688

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc3eb5910883'
down_revision: Union[str, Sequence[str], None] = '71fd3b356683'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('todos', sa.Column('mail_sent', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('todos', 'mail_sent')
