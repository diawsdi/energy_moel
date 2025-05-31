from sqlalchemy import Column, String, ForeignKey, DateTime, func, Enum, JSON, Index
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
    reference_village_id = Column(String, ForeignKey("village_points.id"))
    metadata = Column(JSON)  # For storing additional area-specific data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="areas")
    reference_village = relationship("VillagePoint")

    # Create indexes
    __table_args__ = (
        Index('project_areas_geom_idx', 'geometry', postgresql_using='gist'),
        Index('project_areas_project_idx', 'project_id'),
    )

    def __repr__(self):
        return f"<ProjectArea(id={self.id}, name={self.name}, type={self.area_type})>" 