from sqlalchemy import Column, Integer, Float, String, MetaData
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry

# Create a base for views to avoid ORM creation in database
ViewBase = declarative_base(metadata=MetaData())


class AdminStatisticsView(ViewBase):
    """
    Read-only model for the admin_statistics_view.
    This represents a SQL view joining administrative_boundaries with building_statistics.
    """
    __tablename__ = "admin_statistics_view"

    id = Column(String, primary_key=True)
    name = Column(String)
    level = Column(String)
    level_num = Column(Integer)
    parent_id = Column(String)
    
    # Building counts
    total_buildings = Column(Integer)
    electrified_buildings = Column(Integer)
    high_confidence_50 = Column(Integer)
    high_confidence_60 = Column(Integer)
    high_confidence_70 = Column(Integer)
    high_confidence_80 = Column(Integer)
    high_confidence_85 = Column(Integer)
    high_confidence_90 = Column(Integer)
    unelectrified_buildings = Column(Integer)
    
    # Rates
    electrification_rate = Column(Float)
    high_confidence_rate_50 = Column(Float)
    high_confidence_rate_60 = Column(Float)
    high_confidence_rate_70 = Column(Float)
    high_confidence_rate_80 = Column(Float)
    high_confidence_rate_85 = Column(Float)
    high_confidence_rate_90 = Column(Float)
    
    # Energy metrics
    avg_consumption_kwh_month = Column(Float)
    avg_energy_demand_kwh_year = Column(Float)
    
    # Geometry
    geom = Column(Geometry('MULTIPOLYGON', srid=4326))
    
    def __repr__(self):
        return f"<AdminStatisticsView(id={self.id}, name={self.name}, level={self.level})>"


class AdminStatisticsMaterialized(ViewBase):
    """
    Read-only model for the admin_statistics_materialized materialized view.
    This is a materialized view for better performance.
    """
    __tablename__ = "admin_statistics_materialized"

    id = Column(String, primary_key=True)
    name = Column(String)
    level = Column(String)
    level_num = Column(Integer)
    parent_id = Column(String)
    
    # Building counts
    total_buildings = Column(Integer)
    electrified_buildings = Column(Integer)
    high_confidence_50 = Column(Integer)
    high_confidence_60 = Column(Integer)
    high_confidence_70 = Column(Integer)
    high_confidence_80 = Column(Integer)
    high_confidence_85 = Column(Integer)
    high_confidence_90 = Column(Integer)
    unelectrified_buildings = Column(Integer)
    
    # Rates
    electrification_rate = Column(Float)
    high_confidence_rate_50 = Column(Float)
    high_confidence_rate_60 = Column(Float)
    high_confidence_rate_70 = Column(Float)
    high_confidence_rate_80 = Column(Float)
    high_confidence_rate_85 = Column(Float)
    high_confidence_rate_90 = Column(Float)
    
    # Energy metrics
    avg_consumption_kwh_month = Column(Float)
    avg_energy_demand_kwh_year = Column(Float)
    
    # Geometry
    geom = Column(Geometry('MULTIPOLYGON', srid=4326))
    
    def __repr__(self):
        return f"<AdminStatisticsMaterialized(id={self.id}, name={self.name}, level={self.level})>" 