"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2026-01-05
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Use Base.metadata to create all tables based on SQLAlchemy models.
    bind = op.get_bind()
    from backend.db import Base
    Base.metadata.create_all(bind=bind)


def downgrade():
    bind = op.get_bind()
    from backend.db import Base
    Base.metadata.drop_all(bind=bind)
