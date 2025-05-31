from sqlalchemy import Column, String, ForeignKey, DateTime, func, Index
from geoalchemy2 import Geometry

from app.db.base_class import Base


class VillagePoint(Base):
    __tablename__ = "village_points"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    commune_id = Column(String, ForeignKey("administrative_boundaries.id"), nullable=False)
    geometry = Column(Geometry('POINT', srid=4326), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Create indexes
    __table_args__ = (
        Index('village_points_geom_idx', 'geometry', postgresql_using='gist'),
        Index('village_points_name_idx', 'name'),
        Index('village_points_commune_idx', 'commune_id'),
    )
    
    def __repr__(self):
        return f"<VillagePoint(id={self.id}, name={self.name})>" 