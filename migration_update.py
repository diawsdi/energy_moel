"""Update project area model

Revision ID: e091c1c38f11
Revises: 001
Create Date: 2025-05-31 20:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2 as ga
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e091c1c38f11'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the foreign key constraint on reference_village_id first
    op.drop_constraint('project_areas_reference_village_id_fkey', 'project_areas', type_='foreignkey')
    
    # Drop the reference_village_id column
    op.drop_column('project_areas', 'reference_village_id')
    
    # Add new columns to project_areas table
    op.add_column('project_areas', sa.Column('source_type', sa.Enum('drawn', 'geojson_upload', 'shapefile', name='source_type'), nullable=True))
    op.add_column('project_areas', sa.Column('original_filename', sa.String(), nullable=True))
    op.add_column('project_areas', sa.Column('processing_status', sa.Enum('pending', 'processing', 'completed', 'failed', name='processing_status'), nullable=True))
    op.add_column('project_areas', sa.Column('simplification_tolerance', sa.Float(), nullable=True))
    op.add_column('project_areas', sa.Column('area_sq_km', sa.Float(), nullable=True))


def downgrade():
    # Drop new columns
    op.drop_column('project_areas', 'area_sq_km')
    op.drop_column('project_areas', 'simplification_tolerance')
    op.drop_column('project_areas', 'processing_status')
    op.drop_column('project_areas', 'original_filename')
    op.drop_column('project_areas', 'source_type')
    
    # Add back the reference_village_id column
    op.add_column('project_areas', sa.Column('reference_village_id', sa.String(), nullable=True))
    
    # Add back the foreign key constraint
    op.create_foreign_key('project_areas_reference_village_id_fkey', 'project_areas', 'administrative_boundaries', ['reference_village_id'], ['id'])
