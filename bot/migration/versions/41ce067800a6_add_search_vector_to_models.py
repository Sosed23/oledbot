"""Add search_vector to models

Revision ID: 41ce067800a6
Revises: 043deb47952d
Create Date: 2025-04-11 13:36:37.282623

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR


# revision identifiers, used by Alembic.
revision: str = '41ce067800a6'
down_revision: Union[str, None] = '043deb47952d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        'models',
        sa.Column('search_vector', TSVECTOR, nullable=True)
    )
    op.execute("""
        UPDATE models
        SET search_vector = to_tsvector('english',
            coalesce(model_name, '') || ' ' ||
            coalesce(model_engineer, '') || ' ' ||
            coalesce(model_id, '')
        );
    """)
    op.execute("CREATE INDEX models_search_idx ON models USING GIN(search_vector);")
    op.execute("""
        CREATE TRIGGER models_search_vector_update
        BEFORE INSERT OR UPDATE ON models
        FOR EACH ROW EXECUTE FUNCTION
        tsvector_update_trigger(
            search_vector,
            'pg_catalog.english',
            model_name,
            model_engineer,
            model_id
        );
    """)

def downgrade():
    op.execute("DROP TRIGGER IF EXISTS models_search_vector_update ON models;")
    op.execute("DROP INDEX IF EXISTS models_search_idx;")
    op.drop_column('models', 'search_vector')