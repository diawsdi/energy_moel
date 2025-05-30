from sqlalchemy import Boolean, Column, Float, Integer, String, Index, Text
from sqlalchemy.sql.sqltypes import TIMESTAMP
from geoalchemy2 import Geometry
from geoalchemy2.types import WKBElement

from app.db.base_class import Base


class BuildingsEnergy(Base):
    __tablename__ = "buildings_energy"

    id = Column(Integer, primary_key=True, index=True)
    geom = Column(Geometry('MULTIPOLYGON', srid=4326), nullable=False)
    area_in_meters = Column(Float, nullable=True)
    year = Column(Integer, nullable=False)
    energy_demand_kwh = Column(Float, nullable=True)
    has_access = Column(Boolean, nullable=True)
    building_type = Column(String, nullable=True)
    data_source = Column(String, nullable=True)
    grid_node_id = Column(String, nullable=True)
    origin_id = Column(String, nullable=True)
    
    # ML prediction fields
    predicted_prob = Column(Float, nullable=True)
    predicted_electrified = Column(Integer, nullable=True)
    
    # Energy consumption fields
    consumption_kwh_month = Column(Float, nullable=True)
    std_consumption_kwh_month = Column(Float, nullable=True)
    
    # Origin information
    origin = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP", nullable=False)
    updated_at = Column(
        TIMESTAMP, 
        server_default="CURRENT_TIMESTAMP",
        server_onupdate="CURRENT_TIMESTAMP",
        nullable=False
    )

    # Create indexes
    __table_args__ = (
        Index('idx_buildings_energy_geom', 'geom', postgresql_using='gist'),
        Index('idx_buildings_energy_year', 'year'),
        Index('idx_buildings_energy_has_access', 'has_access'),
        Index('idx_buildings_energy_building_type', 'building_type'),
        Index('idx_buildings_energy_grid_node_id', 'grid_node_id'),
        Index('idx_buildings_energy_predicted_prob', 'predicted_prob'),
        Index('idx_buildings_energy_predicted_electrified', 'predicted_electrified'),
        Index('idx_buildings_energy_consumption_kwh_month', 'consumption_kwh_month'),
    ) 
    
    def __repr__(self):
        return f"<BuildingsEnergy(id={self.id}, has_access={self.has_access}, predicted_prob={self.predicted_prob})>" 