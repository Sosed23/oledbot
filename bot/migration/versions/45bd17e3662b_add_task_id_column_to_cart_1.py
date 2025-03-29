"""add task_id column to Cart_1

Revision ID: 45bd17e3662b
Revises: fe0179091c5b
Create Date: 2025-03-23 18:16:41.880891

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '45bd17e3662b'
down_revision: Union[str, None] = 'fe0179091c5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем новый столбец task_id в таблицу carts
    op.add_column('carts', sa.Column('task_id', sa.Integer(), nullable=True))

def downgrade() -> None:
    # Удаляем task_id при откате миграции
    op.drop_column('carts', 'task_id')