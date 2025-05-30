from sqlalchemy import Column, Integer, BigInteger, Index
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry

from app.db.base_class import Base


class GridNode(Base):
    __tablename__ = "grid_nodes"

    node_id = Column(BigInteger, primary_key=True)
    year = Column(Integer, nullable=False)
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    properties = Column(JSONB, default={})

    __table_args__ = (
        Index('idx_grid_nodes_geom', 'location', postgresql_using='gist'),
        Index('idx_grid_nodes_year', 'year'),
    )

    def __repr__(self):
        return f"<GridNode(node_id={self.node_id}, year={self.year})>"


class GridLine(Base):
    __tablename__ = "grid_lines"

    line_id = Column(BigInteger, primary_key=True)
    year = Column(Integer, nullable=False)
    path = Column(Geometry('LINESTRING', srid=4326), nullable=False)
    properties = Column(JSONB, default={})

    __table_args__ = (
        Index('idx_grid_lines_geom', 'path', postgresql_using='gist'),
        Index('idx_grid_lines_year', 'year'),
    )

    def __repr__(self):
        return f"<GridLine(line_id={self.line_id}, year={self.year})>"


class PowerPlant(Base):
    __tablename__ = "power_plants"

    plant_id = Column(BigInteger, primary_key=True)
    year = Column(Integer, nullable=False)
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    properties = Column(JSONB, default={})

    __table_args__ = (
        Index('idx_power_plants_geom', 'location', postgresql_using='gist'),
        Index('idx_power_plants_year', 'year'),
    )

    def __repr__(self):
        return f"<PowerPlant(plant_id={self.plant_id}, year={self.year})>" 