from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class RegionBasicInfo(BaseModel):
    name: str
    total_buildings: int
    electrification_rate: float
    high_confidence_rate: float


class HighConfidenceRates(BaseModel):
    fifty_percent: float = Field(..., alias="50_percent")
    sixty_percent: float = Field(..., alias="60_percent")
    seventy_percent: float = Field(..., alias="70_percent")
    eighty_percent: float = Field(..., alias="80_percent")
    eightyfive_percent: float = Field(..., alias="85_percent")
    ninety_percent: float = Field(..., alias="90_percent")
    
    class Config:
        populate_by_name = True


class NationalStatistics(BaseModel):
    total_buildings: int
    electrified_buildings: int
    unelectrified_buildings: int
    electrification_rate: float
    high_confidence_rates: HighConfidenceRates
    avg_consumption_kwh_month: float
    avg_energy_demand_kwh_year: float


class RegionInsight(BaseModel):
    name: str
    electrification_rate: float
    total_buildings: int


class ConfidenceGapRegion(BaseModel):
    name: str
    electrification_rate: float
    high_confidence_rate: float
    gap: float


class GeographicInsights(BaseModel):
    top_electrified_regions: List[RegionInsight]
    least_electrified_regions: List[RegionInsight]
    highest_confidence_gap_regions: List[ConfidenceGapRegion]


class ThresholdGap(BaseModel):
    threshold: str
    gap: float


class ConfidenceAnalysis(BaseModel):
    confidence_rate_gap: float
    confidence_rate_gradient: List[ThresholdGap]


class EnergyPlanning(BaseModel):
    total_estimated_monthly_consumption: float
    total_estimated_annual_demand: float
    unmet_annual_demand: float


class NationalMetricsResponse(BaseModel):
    timestamp: datetime
    national_statistics: NationalStatistics
    geographic_insights: GeographicInsights
    confidence_analysis: ConfidenceAnalysis
    energy_planning: EnergyPlanning


class RegionStatistics(BaseModel):
    total_buildings: int
    electrified_buildings: int
    unelectrified_buildings: int
    electrification_rate: float
    high_confidence_rates: HighConfidenceRates
    avg_consumption_kwh_month: float
    avg_energy_demand_kwh_year: float


class DepartmentInfo(BaseModel):
    name: str
    electrification_rate: float
    high_confidence_rate: float
    total_buildings: int


class RegionMetricsResponse(BaseModel):
    timestamp: datetime
    region_name: str
    statistics: RegionStatistics
    departments: List[DepartmentInfo]
    confidence_analysis: ConfidenceAnalysis


class PriorityZone(BaseModel):
    name: str
    level: str
    total_buildings: int
    electrification_rate: float
    high_confidence_rate: float
    confidence_gap: float


class HighDemandZone(BaseModel):
    name: str
    level: str
    total_buildings: int
    electrification_rate: float
    avg_energy_demand_kwh_year: float
    total_unmet_demand_kwh_year: float


class PriorityZonesResponse(BaseModel):
    timestamp: datetime
    electrification_priority_zones: List[PriorityZone]
    verification_priority_zones: List[PriorityZone]
    high_demand_priority_zones: List[HighDemandZone]


class RegionsListResponse(BaseModel):
    timestamp: datetime
    regions: List[RegionBasicInfo]


class CommuneStdDevInfo(BaseModel):
    name: str
    region_name: str
    department_name: str
    total_buildings: int
    electrified_buildings: int
    avg_consumption_kwh_month: float
    avg_std_consumption_kwh_month: float
    std_dev_ratio: float
    uncertainty_category: str


class StdDevCategoryResponse(BaseModel):
    timestamp: datetime
    high_uncertainty_communes: List[CommuneStdDevInfo]
    medium_uncertainty_communes: List[CommuneStdDevInfo]
    low_uncertainty_communes: List[CommuneStdDevInfo]
    statistics: Dict[str, Any]


class AdminAreaInfo(BaseModel):
    name: str
    electrification_rate: float
    high_confidence_rate: float
    total_buildings: int


class AdminMetricsResponse(BaseModel):
    timestamp: datetime
    admin_level: str  # 'region', 'department', 'arrondissement', 'commune'
    admin_name: str
    statistics: RegionStatistics  # We can reuse this as it has all needed fields
    children: List[AdminAreaInfo]  # Child administrative areas
    confidence_analysis: ConfidenceAnalysis 