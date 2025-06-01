from sqlalchemy import Column, String, ForeignKey, DateTime, func, Enum, JSON, Index, Float
from geoalchemy2 import Geometry
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    organization_type = Column(Enum('government', 'private', name='organization_type'), nullable=False)
    status = Column(Enum('draft', 'active', 'completed', 'archived', name='project_status'), 
                   nullable=False, server_default='draft')
    created_by = Column(String, nullable=False)  # Reference to users table
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    areas = relationship("ProjectArea", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name}, status={self.status})>"


class ProjectArea(Base):
    __tablename__ = "project_areas"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    area_type = Column(Enum('village', 'custom', name='area_type'), nullable=False)
    geometry = Column(Geometry('MULTIPOLYGON', srid=4326), nullable=False)
    area_metadata = Column(JSON, name='metadata')  # For storing additional area-specific data
    
    # New fields for handling various geometry inputs
    source_type = Column(Enum('drawn', 'geojson_upload', 'shapefile', name='source_type'), nullable=False)
    original_filename = Column(String, nullable=True)
    processing_status = Column(Enum('pending', 'processing', 'completed', 'failed', name='processing_status'), 
                              nullable=False, server_default='completed')
    simplification_tolerance = Column(Float, nullable=True)  # Tolerance used if geometry was simplified
    area_sq_km = Column(Float, nullable=True)  # Area in square kilometers
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="areas")

    # Create indexes
    __table_args__ = (
        Index('project_areas_geom_idx', 'geometry', postgresql_using='gist'),
        Index('project_areas_project_idx', 'project_id'),
    )

    def __repr__(self):
        return f"<ProjectArea(id={self.id}, name={self.name}, type={self.area_type})>" 