"""Rename username to user_name

Revision ID: f9c43cd33245
Revises: 5bd42880e97c
Create Date: 2025-03-23 18:06:19.267478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9c43cd33245'
down_revision: Union[str, None] = '5bd42880e97c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
