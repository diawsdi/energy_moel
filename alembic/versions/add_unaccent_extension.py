"""add unaccent extension

Revision ID: add_unaccent_extension
Revises: 
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_unaccent_extension'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create the unaccent extension if it doesn't exist
    op.execute('CREATE EXTENSION IF NOT EXISTS unaccent')


def downgrade():
    # Drop the unaccent extension
    op.execute('DROP EXTENSION IF EXISTS unaccent') 