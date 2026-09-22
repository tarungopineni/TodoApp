"""create phonenumber column for Users table

Revision ID: 60fc2a245572
Revises: 
Create Date: 2026-06-14 07:23:56.115079

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60fc2a245572'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users',sa.Column('phonenumber',sa.String(),nullable=True))


def downgrade() -> None:
    op.drop_column('users','phonenumber')