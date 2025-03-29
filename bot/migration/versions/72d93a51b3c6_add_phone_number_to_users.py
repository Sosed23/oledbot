"""Add phone_number to users

Revision ID: 72d93a51b3c6
Revises: 18c47586e78a
Create Date: 2025-03-27 14:01:28.742574

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '72d93a51b3c6'
down_revision: Union[str, None] = '18c47586e78a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('users', sa.Column('phone_number', sa.String(), nullable=True))

def downgrade():
    op.drop_column('users', 'phone_number')
