from sqlalchemy import Column, String, Integer, Index, ForeignKey
from geoalchemy2 import Geometry

from app.db.base_class import Base


class AdministrativeBoundary(Base):
    __tablename__ = "administrative_boundaries"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    level = Column(String, nullable=False)
    level_num = Column(Integer, nullable=False)
    parent_id = Column(String, ForeignKey("administrative_boundaries.id"), nullable=True)
    geom = Column(Geometry('MULTIPOLYGON', srid=4326), nullable=False)

    # Create indexes
    __table_args__ = (
        Index('admin_boundaries_geom_idx', 'geom', postgresql_using='gist'),
        Index('admin_boundaries_level_idx', 'level'),
        Index('admin_boundaries_parent_idx', 'parent_id'),
    )
    
    def __repr__(self):
        return f"<AdministrativeBoundary(id={self.id}, name={self.name}, level={self.level})>" 