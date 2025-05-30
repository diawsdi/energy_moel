from sqlalchemy import Column, String, Integer, Float, ForeignKey, Index, TIMESTAMP
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class BuildingStatistics(Base):
    __tablename__ = "building_statistics"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(String, ForeignKey("administrative_boundaries.id"), unique=True)
    
    # Building counts
    total_buildings = Column(Integer, default=0)
    electrified_buildings = Column(Integer, default=0)
    high_confidence_50 = Column(Integer, default=0)
    high_confidence_60 = Column(Integer, default=0)
    high_confidence_70 = Column(Integer, default=0)
    high_confidence_80 = Column(Integer, default=0)
    high_confidence_85 = Column(Integer, default=0)
    high_confidence_90 = Column(Integer, default=0)
    unelectrified_buildings = Column(Integer, default=0)
    
    # Rates
    electrification_rate = Column(Float, default=0)
    high_confidence_rate_50 = Column(Float, default=0)
    high_confidence_rate_60 = Column(Float, default=0)
    high_confidence_rate_70 = Column(Float, default=0)
    high_confidence_rate_80 = Column(Float, default=0)
    high_confidence_rate_85 = Column(Float, default=0)
    high_confidence_rate_90 = Column(Float, default=0)
    
    # Energy metrics
    avg_consumption_kwh_month = Column(Float, default=0)
    avg_energy_demand_kwh_year = Column(Float, default=0)
    
    # Timestamps
    updated_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP", onupdate="CURRENT_TIMESTAMP")
    
    def __repr__(self):
        return f"<BuildingStatistics(id={self.id}, admin_id={self.admin_id}, total_buildings={self.total_buildings})>" 