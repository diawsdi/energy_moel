from sqlalchemy import Column, Integer, Float, String, Index, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry

from app.db.base_class import Base


class UnelectrifiedCluster(Base):
    __tablename__ = "unelectrified_clusters"

    cluster_id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    area = Column(Geometry('POLYGON', srid=4326), nullable=False)
    properties = Column(JSONB, nullable=False)
    total_buildings = Column(Integer)
    total_energy_kwh = Column(Float)
    avg_energy_kwh = Column(Float)

    __table_args__ = (
        Index('unelectrified_clusters_area_idx', 'area', postgresql_using='gist'),
        Index('unelectrified_clusters_year_idx', 'year'),
    )

    def __repr__(self):
        return f"<UnelectrifiedCluster(cluster_id={self.cluster_id}, total_buildings={self.total_buildings})>"


class UnelectrifiedBuilding(Base):
    __tablename__ = "unelectrified_buildings"

    id = Column(Integer, primary_key=True)
    origin = Column(String)
    origin_id = Column(String)
    origin_origin_id = Column(String)
    area_in_meters = Column(Float)
    n_bldgs_1km_away = Column(Integer)
    lulc2023_built_area_n1 = Column(Float)
    lulc2023_rangeland_n1 = Column(Float)
    lulc2023_crops_n1 = Column(Float)
    lulc2023_built_area_n11 = Column(Float)
    lulc2023_rangeland_n11 = Column(Float)
    lulc2023_crops_n11 = Column(Float)
    ntl2023_n1 = Column(Float)
    ntl2023_n11 = Column(Float)
    ookla_fixed_20230101_avg_d_kbps = Column(Float)
    ookla_fixed_20230101_devices = Column(Integer)
    ookla_mobile_20230101_avg_d_kbps = Column(Float)
    ookla_mobile_20230101_devices = Column(Integer)
    predicted_prob = Column(Float)
    predicted_electrified = Column(Integer)
    consumption_kwh_month = Column(Float)
    std_consumption_kwh_month = Column(Float)
    geom = Column(Geometry('POLYGON', srid=4326))

    __table_args__ = (
        Index('unelectrified_buildings_geom_idx', 'geom', postgresql_using='gist'),
    )

    def __repr__(self):
        return f"<UnelectrifiedBuilding(id={self.id}, predicted_prob={self.predicted_prob})>" 