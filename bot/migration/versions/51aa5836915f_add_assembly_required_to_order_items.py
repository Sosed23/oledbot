"""add assembly_required to order_items

Revision ID: 51aa5836915f
Revises: 41ce067800a6
Create Date: 2025-04-20 00:12:04.248139

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51aa5836915f'
down_revision: Union[str, None] = '41ce067800a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('carts', sa.Column('assembly_required', sa.Boolean(), nullable=False))
    op.add_column('carts', sa.Column('touch_or_backlight', sa.Boolean(), nullable=False))
    op.drop_index('models_search_idx', table_name='models', postgresql_using='gin')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('models_search_idx', 'models', ['search_vector'], unique=False, postgresql_using='gin')
    op.drop_column('carts', 'touch_or_backlight')
    op.drop_column('carts', 'assembly_required')
    # ### end Alembic commands ###
