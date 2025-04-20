"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2023-12-01

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2 as ga


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create PostGIS extension - skip if already exists
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    
    # Check if the table exists before creating it
    conn = op.get_bind()
    res = conn.execute(sa.text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'buildings_energy')"))
    table_exists = res.scalar()
    
    if not table_exists:
        # Create buildings_energy table
        op.create_table('buildings_energy',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('geom', ga.Geometry(geometry_type='MULTIPOLYGON', srid=4326), nullable=False),
            sa.Column('area_in_meters', sa.Float(), nullable=True),
            sa.Column('year', sa.Integer(), nullable=False),
            sa.Column('energy_demand_kwh', sa.Float(), nullable=True),
            sa.Column('has_access', sa.Boolean(), nullable=True),
            sa.Column('building_type', sa.String(), nullable=True),
            sa.Column('data_source', sa.String(), nullable=True),
            sa.Column('grid_node_id', sa.String(), nullable=True),
            sa.Column('origin_id', sa.String(), nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), server_onupdate=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes
        op.create_index('idx_buildings_energy_geom', 'buildings_energy', ['geom'], unique=False, postgresql_using='gist')
        op.create_index('idx_buildings_energy_year', 'buildings_energy', ['year'], unique=False)
        op.create_index('idx_buildings_energy_has_access', 'buildings_energy', ['has_access'], unique=False)
        op.create_index('idx_buildings_energy_building_type', 'buildings_energy', ['building_type'], unique=False)
        op.create_index('idx_buildings_energy_grid_node_id', 'buildings_energy', ['grid_node_id'], unique=False)
        op.create_index(op.f('ix_buildings_energy_id'), 'buildings_energy', ['id'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_buildings_energy_id'), table_name='buildings_energy')
    op.drop_index('idx_buildings_energy_grid_node_id', table_name='buildings_energy')
    op.drop_index('idx_buildings_energy_building_type', table_name='buildings_energy')
    op.drop_index('idx_buildings_energy_has_access', table_name='buildings_energy')
    op.drop_index('idx_buildings_energy_year', table_name='buildings_energy')
    op.drop_index('idx_buildings_energy_geom', table_name='buildings_energy')
    
    # Drop table
    op.drop_table('buildings_energy') 