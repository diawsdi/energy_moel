from typing import Any, Dict, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.db.deps import get_db
from app import schemas

router = APIRouter()


@router.get("/national", response_model=schemas.metrics.NationalMetricsResponse)
def get_national_metrics(
    db: Session = Depends(get_db),
) -> Any:
    """
    Get national-level electrification metrics.
    Returns overall statistics for the entire country.
    """
    try:
        # Get total buildings and electrification rates using raw SQL for complex calculations
        national_stats_query = """
        SELECT 
            SUM(total_buildings) as total_buildings,
            SUM(electrified_buildings) as electrified_buildings,
            SUM(unelectrified_buildings) as unelectrified_buildings,
            CASE 
                WHEN SUM(total_buildings) > 0 
                THEN (SUM(electrified_buildings)::float / SUM(total_buildings)::float) * 100 
                ELSE 0 
            END as electrification_rate,
            CASE 
                WHEN SUM(total_buildings) > 0 
                THEN (SUM(high_confidence_50)::float / SUM(total_buildings)::float) * 100 
                ELSE 0 
            END as high_confidence_rate_50,
            CASE 
                WHEN SUM(total_buildings) > 0 
                THEN (SUM(high_confidence_60)::float / SUM(total_buildings)::float) * 100 
                ELSE 0 
            END as high_confidence_rate_60,
            CASE 
                WHEN SUM(total_buildings) > 0 
                THEN (SUM(high_confidence_70)::float / SUM(total_buildings)::float) * 100 
                ELSE 0 
            END as high_confidence_rate_70,
            CASE 
                WHEN SUM(total_buildings) > 0 
                THEN (SUM(high_confidence_80)::float / SUM(total_buildings)::float) * 100 
                ELSE 0 
            END as high_confidence_rate_80,
            CASE 
                WHEN SUM(total_buildings) > 0 
                THEN (SUM(high_confidence_85)::float / SUM(total_buildings)::float) * 100 
                ELSE 0 
            END as high_confidence_rate_85,
            CASE 
                WHEN SUM(total_buildings) > 0 
                THEN (SUM(high_confidence_90)::float / SUM(total_buildings)::float) * 100 
                ELSE 0 
            END as high_confidence_rate_90,
            AVG(avg_consumption_kwh_month) as avg_consumption_kwh_month,
            AVG(avg_energy_demand_kwh_year) as avg_energy_demand_kwh_year
        FROM building_statistics
        WHERE admin_id IN (
            SELECT id FROM administrative_boundaries WHERE level = 'region'
        )
        """
        
        national_stats_result = db.execute(text(national_stats_query)).fetchone()
        
        if not national_stats_result:
            raise HTTPException(status_code=404, detail="No data found")
        
        # Get top electrified regions
        top_regions_query = """
        SELECT 
            ab.name,
            bs.electrification_rate,
            bs.total_buildings
        FROM 
            building_statistics bs
        JOIN 
            administrative_boundaries ab ON bs.admin_id = ab.id
        WHERE 
            ab.level = 'region'
        ORDER BY 
            bs.electrification_rate DESC
        LIMIT 3
        """
        
        top_regions_result = db.execute(text(top_regions_query)).fetchall()
        top_regions = [
            {
                "name": row[0],
                "electrification_rate": float(row[1]),
                "total_buildings": int(row[2])
            }
            for row in top_regions_result
        ]
        
        # Get least electrified regions
        least_regions_query = """
        SELECT 
            ab.name,
            bs.electrification_rate,
            bs.total_buildings
        FROM 
            building_statistics bs
        JOIN 
            administrative_boundaries ab ON bs.admin_id = ab.id
        WHERE 
            ab.level = 'region'
        ORDER BY 
            bs.electrification_rate ASC
        LIMIT 3
        """
        
        least_regions_result = db.execute(text(least_regions_query)).fetchall()
        least_regions = [
            {
                "name": row[0],
                "electrification_rate": float(row[1]),
                "total_buildings": int(row[2])
            }
            for row in least_regions_result
        ]
        
        # Get confidence gap analysis
        confidence_gap_query = """
        SELECT 
            ab.name,
            bs.electrification_rate,
            bs.high_confidence_rate_90,
            (bs.electrification_rate - bs.high_confidence_rate_90) as confidence_gap
        FROM 
            building_statistics bs
        JOIN 
            administrative_boundaries ab ON bs.admin_id = ab.id
        WHERE 
            ab.level = 'region'
        ORDER BY 
            confidence_gap DESC
        LIMIT 3
        """
        
        confidence_gap_result = db.execute(text(confidence_gap_query)).fetchall()
        confidence_gap = [
            {
                "name": row[0],
                "electrification_rate": float(row[1]),
                "high_confidence_rate": float(row[2]),
                "gap": float(row[3])
            }
            for row in confidence_gap_result
        ]
        
        # Construct the response
        response = {
            "timestamp": datetime.now().isoformat(),
            "national_statistics": {
                "total_buildings": int(national_stats_result[0]),
                "electrified_buildings": int(national_stats_result[1]),
                "unelectrified_buildings": int(national_stats_result[2]),
                "electrification_rate": float(national_stats_result[3]),
                "high_confidence_rates": {
                    "50_percent": float(national_stats_result[4]),
                    "60_percent": float(national_stats_result[5]),
                    "70_percent": float(national_stats_result[6]),
                    "80_percent": float(national_stats_result[7]),
                    "85_percent": float(national_stats_result[8]),
                    "90_percent": float(national_stats_result[9])
                },
                "avg_consumption_kwh_month": float(national_stats_result[10]),
                "avg_energy_demand_kwh_year": float(national_stats_result[11])
            },
            "geographic_insights": {
                "top_electrified_regions": top_regions,
                "least_electrified_regions": least_regions,
                "highest_confidence_gap_regions": confidence_gap
            },
            "confidence_analysis": {
                "confidence_rate_gap": float(national_stats_result[3]) - float(national_stats_result[9]),
                "confidence_rate_gradient": [
                    {"threshold": "50%", "gap": float(national_stats_result[3]) - float(national_stats_result[4])},
                    {"threshold": "60%", "gap": float(national_stats_result[3]) - float(national_stats_result[5])},
                    {"threshold": "70%", "gap": float(national_stats_result[3]) - float(national_stats_result[6])},
                    {"threshold": "80%", "gap": float(national_stats_result[3]) - float(national_stats_result[7])},
                    {"threshold": "85%", "gap": float(national_stats_result[3]) - float(national_stats_result[8])},
                    {"threshold": "90%", "gap": float(national_stats_result[3]) - float(national_stats_result[9])}
                ]
            }
        }
        
        # Calculate energy planning metrics
        response["energy_planning"] = {
            "total_estimated_monthly_consumption": response["national_statistics"]["electrified_buildings"] * 
                                               response["national_statistics"]["avg_consumption_kwh_month"],
            "total_estimated_annual_demand": response["national_statistics"]["total_buildings"] * 
                                           response["national_statistics"]["avg_energy_demand_kwh_year"],
            "unmet_annual_demand": response["national_statistics"]["unelectrified_buildings"] * 
                                  response["national_statistics"]["avg_energy_demand_kwh_year"]
        }
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/region/{region_name}", response_model=schemas.metrics.RegionMetricsResponse)
def get_region_metrics(
    region_name: str = Path(..., description="The name of the region"),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get metrics for a specific region by name.
    Returns detailed statistics for the specified region.
    """
    try:
        # Get region statistics
        region_query = """
        SELECT 
            bs.total_buildings,
            bs.electrified_buildings,
            bs.unelectrified_buildings,
            bs.electrification_rate,
            bs.high_confidence_rate_50,
            bs.high_confidence_rate_60,
            bs.high_confidence_rate_70,
            bs.high_confidence_rate_80,
            bs.high_confidence_rate_85,
            bs.high_confidence_rate_90,
            bs.avg_consumption_kwh_month,
            bs.avg_energy_demand_kwh_year
        FROM 
            building_statistics bs
        JOIN 
            administrative_boundaries ab ON bs.admin_id = ab.id
        WHERE 
            ab.level = 'region' AND
            ab.name = :region_name
        """
        
        region_result = db.execute(text(region_query), {"region_name": region_name}).fetchone()
        
        if not region_result:
            raise HTTPException(status_code=404, detail=f"Region '{region_name}' not found")
        
        # Get departments in this region
        departments_query = """
        SELECT 
            ab.name,
            bs.electrification_rate,
            bs.high_confidence_rate_90,
            bs.total_buildings
        FROM 
            building_statistics bs
        JOIN 
            administrative_boundaries ab ON bs.admin_id = ab.id
        JOIN 
            administrative_boundaries parent ON ab.parent_id = parent.id
        WHERE 
            ab.level = 'department' AND
            parent.name = :region_name
        ORDER BY 
            bs.electrification_rate DESC
        """
        
        departments_result = db.execute(text(departments_query), {"region_name": region_name}).fetchall()
        departments = [
            {
                "name": row[0],
                "electrification_rate": float(row[1]),
                "high_confidence_rate": float(row[2]),
                "total_buildings": int(row[3])
            }
            for row in departments_result
        ]
        
        # Construct the response
        response = {
            "timestamp": datetime.now().isoformat(),
            "region_name": region_name,
            "statistics": {
                "total_buildings": int(region_result[0]),
                "electrified_buildings": int(region_result[1]),
                "unelectrified_buildings": int(region_result[2]),
                "electrification_rate": float(region_result[3]),
                "high_confidence_rates": {
                    "50_percent": float(region_result[4]),
                    "60_percent": float(region_result[5]),
                    "70_percent": float(region_result[6]),
                    "80_percent": float(region_result[7]),
                    "85_percent": float(region_result[8]),
                    "90_percent": float(region_result[9])
                },
                "avg_consumption_kwh_month": float(region_result[10]),
                "avg_energy_demand_kwh_year": float(region_result[11])
            },
            "departments": departments,
            "confidence_analysis": {
                "confidence_rate_gap": float(region_result[3]) - float(region_result[9]),
                "confidence_rate_gradient": [
                    {"threshold": "50%", "gap": float(region_result[3]) - float(region_result[4])},
                    {"threshold": "60%", "gap": float(region_result[3]) - float(region_result[5])},
                    {"threshold": "70%", "gap": float(region_result[3]) - float(region_result[6])},
                    {"threshold": "80%", "gap": float(region_result[3]) - float(region_result[7])},
                    {"threshold": "85%", "gap": float(region_result[3]) - float(region_result[8])},
                    {"threshold": "90%", "gap": float(region_result[3]) - float(region_result[9])}
                ]
            }
        }
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/priority-zones", response_model=schemas.metrics.PriorityZonesResponse)
def get_priority_zones(
    db: Session = Depends(get_db),
) -> Any:
    """
    Get priority zones for electrification planning.
    Returns areas with highest needs based on population density, 
    low electrification, and high confidence gaps.
    """
    try:
        # Get priority zones based on building density and low electrification
        priority_zones_query = """
        SELECT 
            ab.name,
            ab.level,
            bs.total_buildings,
            bs.electrification_rate,
            bs.high_confidence_rate_90,
            (bs.electrification_rate - bs.high_confidence_rate_90) as confidence_gap
        FROM 
            building_statistics bs
        JOIN 
            administrative_boundaries ab ON bs.admin_id = ab.id
        WHERE 
            ab.level = 'commune' AND
            bs.total_buildings > 100
        ORDER BY 
            bs.electrification_rate ASC,
            bs.total_buildings DESC
        LIMIT 10
        """
        
        priority_zones_result = db.execute(text(priority_zones_query)).fetchall()
        priority_zones = [
            {
                "name": row[0],
                "level": row[1],
                "total_buildings": int(row[2]),
                "electrification_rate": float(row[3]),
                "high_confidence_rate": float(row[4]),
                "confidence_gap": float(row[5])
            }
            for row in priority_zones_result
        ]
        
        # Get verification priority zones (high confidence gap)
        verification_zones_query = """
        SELECT 
            ab.name,
            ab.level,
            bs.total_buildings,
            bs.electrification_rate,
            bs.high_confidence_rate_90,
            (bs.electrification_rate - bs.high_confidence_rate_90) as confidence_gap
        FROM 
            building_statistics bs
        JOIN 
            administrative_boundaries ab ON bs.admin_id = ab.id
        WHERE 
            ab.level = 'commune' AND
            bs.total_buildings > 50
        ORDER BY 
            confidence_gap DESC
        LIMIT 10
        """
        
        verification_zones_result = db.execute(text(verification_zones_query)).fetchall()
        verification_zones = [
            {
                "name": row[0],
                "level": row[1],
                "total_buildings": int(row[2]),
                "electrification_rate": float(row[3]),
                "high_confidence_rate": float(row[4]),
                "confidence_gap": float(row[5])
            }
            for row in verification_zones_result
        ]
        
        # Get high demand zones
        high_demand_zones_query = """
        SELECT 
            ab.name,
            ab.level,
            bs.total_buildings,
            bs.electrification_rate,
            bs.avg_energy_demand_kwh_year,
            (bs.unelectrified_buildings * bs.avg_energy_demand_kwh_year) as total_unmet_demand
        FROM 
            building_statistics bs
        JOIN 
            administrative_boundaries ab ON bs.admin_id = ab.id
        WHERE 
            ab.level = 'commune' AND
            bs.electrification_rate < 80
        ORDER BY 
            total_unmet_demand DESC
        LIMIT 10
        """
        
        high_demand_zones_result = db.execute(text(high_demand_zones_query)).fetchall()
        high_demand_zones = [
            {
                "name": row[0],
                "level": row[1],
                "total_buildings": int(row[2]),
                "electrification_rate": float(row[3]),
                "avg_energy_demand_kwh_year": float(row[4]),
                "total_unmet_demand_kwh_year": float(row[5])
            }
            for row in high_demand_zones_result
        ]
        
        # Construct the response
        response = {
            "timestamp": datetime.now().isoformat(),
            "electrification_priority_zones": priority_zones,
            "verification_priority_zones": verification_zones,
            "high_demand_priority_zones": high_demand_zones
        }
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regions", response_model=schemas.metrics.RegionsListResponse)
def get_all_regions(
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a list of all regions with basic stats.
    Useful for creating dashboards and selectors.
    """
    try:
        regions_query = """
        SELECT 
            ab.name,
            bs.total_buildings,
            bs.electrification_rate,
            bs.high_confidence_rate_90
        FROM 
            building_statistics bs
        JOIN 
            administrative_boundaries ab ON bs.admin_id = ab.id
        WHERE 
            ab.level = 'region'
        ORDER BY 
            ab.name
        """
        
        regions_result = db.execute(text(regions_query)).fetchall()
        regions = [
            {
                "name": row[0],
                "total_buildings": int(row[1]),
                "electrification_rate": float(row[2]),
                "high_confidence_rate": float(row[3])
            }
            for row in regions_result
        ]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "regions": regions
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/uncertainty-analysis", response_model=schemas.metrics.StdDevCategoryResponse)
def get_consumption_uncertainty_analysis(
    db: Session = Depends(get_db),
) -> Any:
    """
    Analyze communes based on their consumption standard deviation.
    
    This endpoint categorizes communes into high, medium, and low uncertainty groups
    based on the standard deviation of their energy consumption estimates.
    This helps identify areas where energy demand estimation needs improvement.
    """
    try:
        # Define a simpler query for the consumption standard deviation analysis
        commune_query = """
        WITH building_samples AS (
            -- Sample buildings to improve query performance
            SELECT 
                id, geom, consumption_kwh_month, std_consumption_kwh_month, has_access
            FROM 
                buildings_energy
            WHERE 
                consumption_kwh_month IS NOT NULL
                AND std_consumption_kwh_month IS NOT NULL
            LIMIT 100000
        ),
        admin_hierarchy AS (
            -- Get the administrative hierarchy information
            SELECT 
                commune.id AS commune_id, 
                commune.name AS commune_name,
                dept.name AS department_name,
                region.name AS region_name,
                commune.geom AS geom
            FROM 
                administrative_boundaries commune
            JOIN 
                administrative_boundaries dept ON commune.parent_id = dept.id
            JOIN 
                administrative_boundaries region ON dept.parent_id = region.id
            WHERE 
                commune.level = 'commune'
        ),
        commune_stats AS (
            -- Calculate statistics per commune
            SELECT 
                ah.commune_id,
                ah.commune_name,
                ah.department_name, 
                ah.region_name,
                COUNT(bs.id) AS total_buildings,
                SUM(CASE WHEN bs.has_access = true THEN 1 ELSE 0 END) AS electrified_buildings,
                AVG(bs.consumption_kwh_month) AS avg_consumption_kwh_month,
                AVG(bs.std_consumption_kwh_month) AS avg_std_consumption_kwh_month,
                CASE 
                    WHEN AVG(bs.consumption_kwh_month) > 0 
                    THEN AVG(bs.std_consumption_kwh_month) / AVG(bs.consumption_kwh_month)
                    ELSE 0 
                END AS std_dev_ratio
            FROM 
                admin_hierarchy ah
            JOIN 
                building_samples bs ON ST_Contains(ah.geom, bs.geom)
            GROUP BY 
                ah.commune_id, ah.commune_name, ah.department_name, ah.region_name
            HAVING 
                COUNT(bs.id) >= 10
        )
        -- Calculate percentiles and return data
        SELECT 
            commune_name,
            department_name,
            region_name,
            total_buildings,
            electrified_buildings,
            avg_consumption_kwh_month,
            avg_std_consumption_kwh_month,
            std_dev_ratio,
            (SELECT percentile_cont(0.33) WITHIN GROUP (ORDER BY std_dev_ratio) FROM commune_stats) AS percentile_33,
            (SELECT percentile_cont(0.67) WITHIN GROUP (ORDER BY std_dev_ratio) FROM commune_stats) AS percentile_67,
            (SELECT AVG(std_dev_ratio) FROM commune_stats) AS avg_ratio,
            (SELECT STDDEV(std_dev_ratio) FROM commune_stats) AS stddev_ratio
        FROM 
            commune_stats
        ORDER BY 
            std_dev_ratio DESC;
        """
        
        result = db.execute(text(commune_query)).fetchall()
        
        if not result or len(result) == 0:
            raise HTTPException(status_code=404, detail="No commune data found")
        
        # Get the percentile values from the first row
        percentile_33 = float(result[0][8]) if result[0][8] is not None else 0.0
        percentile_67 = float(result[0][9]) if result[0][9] is not None else 0.0
        avg_ratio = float(result[0][10]) if result[0][10] is not None else 0.0
        stddev_ratio = float(result[0][11]) if result[0][11] is not None else 0.0
        
        # Categorize communes based on percentiles
        high_uncertainty = []
        medium_uncertainty = []
        low_uncertainty = []
        
        for row in result:
            commune_info = {
                "name": row[0],  # commune_name
                "department_name": row[1],
                "region_name": row[2],
                "total_buildings": int(row[3]) if row[3] is not None else 0,
                "electrified_buildings": int(row[4]) if row[4] is not None else 0,
                "avg_consumption_kwh_month": float(row[5]) if row[5] is not None else 0.0,
                "avg_std_consumption_kwh_month": float(row[6]) if row[6] is not None else 0.0,
                "std_dev_ratio": float(row[7]) if row[7] is not None else 0.0,
                "uncertainty_category": ""
            }
            
            # Categorize based on std_dev_ratio
            if commune_info["std_dev_ratio"] >= percentile_67:
                commune_info["uncertainty_category"] = "high"
                high_uncertainty.append(commune_info)
            elif commune_info["std_dev_ratio"] <= percentile_33:
                commune_info["uncertainty_category"] = "low"
                low_uncertainty.append(commune_info)
            else:
                commune_info["uncertainty_category"] = "medium"
                medium_uncertainty.append(commune_info)
        
        # Create statistics summary
        statistics = {
            "total_communes_analyzed": len(result),
            "percentile_33_threshold": percentile_33,
            "percentile_67_threshold": percentile_67,
            "average_std_dev_ratio": avg_ratio,
            "std_dev_of_ratios": stddev_ratio,
            "high_uncertainty_count": len(high_uncertainty),
            "medium_uncertainty_count": len(medium_uncertainty),
            "low_uncertainty_count": len(low_uncertainty)
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "high_uncertainty_communes": high_uncertainty[:20] if high_uncertainty else [],
            "medium_uncertainty_communes": medium_uncertainty[:20] if medium_uncertainty else [],
            "low_uncertainty_communes": low_uncertainty[:20] if low_uncertainty else [],
            "statistics": statistics
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ranges")
def get_metrics_ranges(
    admin_level: str = Query(None, description="Filter by specific admin level (region, department, arrondissement, commune)"),
    exclude_zero: bool = Query(False, description="Exclude zero values from min calculation"),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get min/max ranges for all metrics to help with dynamic legend generation.
    Returns min and max values for each metric across all administrative levels.
    
    Query parameters:
    - admin_level: Filter by specific admin level (region, department, arrondissement, commune)
    - exclude_zero: Exclude zero values from min calculation (default: false)
    """
    try:
        # Build WHERE clause
        where_clause = ""
        where_params = {}
        
        if admin_level:
            where_clause = "WHERE ab.level = :admin_level"
            where_params["admin_level"] = admin_level
        
        # Build min calculation clause
        min_clause = "MIN" if not exclude_zero else "MIN(NULLIF"
        min_suffix = "" if not exclude_zero else ", 0))"
        
        # Query for all metric ranges
        query = f"""
        SELECT 
            -- Basic building metrics
            {min_clause}(bs.total_buildings){min_suffix} as min_total_buildings,
            MAX(bs.total_buildings) as max_total_buildings,
            {min_clause}(bs.electrified_buildings){min_suffix} as min_electrified_buildings,
            MAX(bs.electrified_buildings) as max_electrified_buildings,
            {min_clause}(bs.unelectrified_buildings){min_suffix} as min_unelectrified_buildings,
            MAX(bs.unelectrified_buildings) as max_unelectrified_buildings,
            
            -- Electrification rates
            {min_clause}(bs.electrification_rate){min_suffix} as min_electrification_rate,
            MAX(bs.electrification_rate) as max_electrification_rate,
            
            -- High confidence rates
            {min_clause}(bs.high_confidence_rate_50){min_suffix} as min_high_confidence_rate_50,
            MAX(bs.high_confidence_rate_50) as max_high_confidence_rate_50,
            {min_clause}(bs.high_confidence_rate_60){min_suffix} as min_high_confidence_rate_60,
            MAX(bs.high_confidence_rate_60) as max_high_confidence_rate_60,
            {min_clause}(bs.high_confidence_rate_70){min_suffix} as min_high_confidence_rate_70,
            MAX(bs.high_confidence_rate_70) as max_high_confidence_rate_70,
            {min_clause}(bs.high_confidence_rate_80){min_suffix} as min_high_confidence_rate_80,
            MAX(bs.high_confidence_rate_80) as max_high_confidence_rate_80,
            {min_clause}(bs.high_confidence_rate_85){min_suffix} as min_high_confidence_rate_85,
            MAX(bs.high_confidence_rate_85) as max_high_confidence_rate_85,
            {min_clause}(bs.high_confidence_rate_90){min_suffix} as min_high_confidence_rate_90,
            MAX(bs.high_confidence_rate_90) as max_high_confidence_rate_90,
            
            -- Energy consumption and demand
            {min_clause}(bs.avg_consumption_kwh_month){min_suffix} as min_avg_consumption_kwh_month,
            MAX(bs.avg_consumption_kwh_month) as max_avg_consumption_kwh_month,
            {min_clause}(bs.avg_energy_demand_kwh_year){min_suffix} as min_avg_energy_demand_kwh_year,
            MAX(bs.avg_energy_demand_kwh_year) as max_avg_energy_demand_kwh_year,
            
            -- Calculated total consumption and demand
            {min_clause}(bs.total_buildings * bs.avg_consumption_kwh_month){min_suffix} as min_total_monthly_consumption,
            MAX(bs.total_buildings * bs.avg_consumption_kwh_month) as max_total_monthly_consumption,
            {min_clause}(bs.total_buildings * bs.avg_energy_demand_kwh_year){min_suffix} as min_total_yearly_demand,
            MAX(bs.total_buildings * bs.avg_energy_demand_kwh_year) as max_total_yearly_demand
        FROM 
            building_statistics bs
        JOIN 
            administrative_boundaries ab ON bs.admin_id = ab.id
        {where_clause}
        """
        
        ranges_result = db.execute(text(query), where_params).fetchone()
        
        if not ranges_result:
            raise HTTPException(status_code=404, detail="No data found")
        
        # Construct response with proper null handling
        response = {
            "timestamp": datetime.now().isoformat(),
            "admin_level_filter": admin_level,
            "exclude_zero_from_min": exclude_zero,
            "ranges": {
                "total_buildings": {
                    "min": float(ranges_result[0]) if ranges_result[0] is not None else 0,
                    "max": float(ranges_result[1]) if ranges_result[1] is not None else 0
                },
                "electrified_buildings": {
                    "min": float(ranges_result[2]) if ranges_result[2] is not None else 0,
                    "max": float(ranges_result[3]) if ranges_result[3] is not None else 0
                },
                "unelectrified_buildings": {
                    "min": float(ranges_result[4]) if ranges_result[4] is not None else 0,
                    "max": float(ranges_result[5]) if ranges_result[5] is not None else 0
                },
                "electrification_rate": {
                    "min": float(ranges_result[6]) if ranges_result[6] is not None else 0,
                    "max": float(ranges_result[7]) if ranges_result[7] is not None else 100
                },
                "high_confidence_rate_50": {
                    "min": float(ranges_result[8]) if ranges_result[8] is not None else 0,
                    "max": float(ranges_result[9]) if ranges_result[9] is not None else 100
                },
                "high_confidence_rate_60": {
                    "min": float(ranges_result[10]) if ranges_result[10] is not None else 0,
                    "max": float(ranges_result[11]) if ranges_result[11] is not None else 100
                },
                "high_confidence_rate_70": {
                    "min": float(ranges_result[12]) if ranges_result[12] is not None else 0,
                    "max": float(ranges_result[13]) if ranges_result[13] is not None else 100
                },
                "high_confidence_rate_80": {
                    "min": float(ranges_result[14]) if ranges_result[14] is not None else 0,
                    "max": float(ranges_result[15]) if ranges_result[15] is not None else 100
                },
                "high_confidence_rate_85": {
                    "min": float(ranges_result[16]) if ranges_result[16] is not None else 0,
                    "max": float(ranges_result[17]) if ranges_result[17] is not None else 100
                },
                "high_confidence_rate_90": {
                    "min": float(ranges_result[18]) if ranges_result[18] is not None else 0,
                    "max": float(ranges_result[19]) if ranges_result[19] is not None else 100
                },
                "avg_consumption_kwh_month": {
                    "min": float(ranges_result[20]) if ranges_result[20] is not None else 0,
                    "max": float(ranges_result[21]) if ranges_result[21] is not None else 0
                },
                "avg_energy_demand_kwh_year": {
                    "min": float(ranges_result[22]) if ranges_result[22] is not None else 0,
                    "max": float(ranges_result[23]) if ranges_result[23] is not None else 0
                },
                "total_monthly_consumption": {
                    "min": float(ranges_result[24]) if ranges_result[24] is not None else 0,
                    "max": float(ranges_result[25]) if ranges_result[25] is not None else 0
                },
                "total_yearly_demand": {
                    "min": float(ranges_result[26]) if ranges_result[26] is not None else 0,
                    "max": float(ranges_result[27]) if ranges_result[27] is not None else 0
                }
            }
        }
        
        # Calculate some helpful derived values
        response["derived_insights"] = {
            "building_density_range": {
                "description": "Range of building density across areas",
                "min": response["ranges"]["total_buildings"]["min"],
                "max": response["ranges"]["total_buildings"]["max"]
            },
            "electrification_gap": {
                "description": "Electrification rate gap (100% - max rate)",
                "gap": 100 - response["ranges"]["electrification_rate"]["max"]
            },
            "confidence_variation": {
                "description": "Variation in 90% confidence rates",
                "min": response["ranges"]["high_confidence_rate_90"]["min"],
                "max": response["ranges"]["high_confidence_rate_90"]["max"],
                "spread": response["ranges"]["high_confidence_rate_90"]["max"] - response["ranges"]["high_confidence_rate_90"]["min"]
            },
            "consumption_scale": {
                "description": "Scale of total monthly consumption values",
                "min_gwh": response["ranges"]["total_monthly_consumption"]["min"] / 1000000,
                "max_gwh": response["ranges"]["total_monthly_consumption"]["max"] / 1000000,
                "min_mwh": response["ranges"]["total_monthly_consumption"]["min"] / 1000,
                "max_mwh": response["ranges"]["total_monthly_consumption"]["max"] / 1000
            },
            "demand_scale": {
                "description": "Scale of total yearly demand values", 
                "min_gwh": response["ranges"]["total_yearly_demand"]["min"] / 1000000,
                "max_gwh": response["ranges"]["total_yearly_demand"]["max"] / 1000000,
                "min_mwh": response["ranges"]["total_yearly_demand"]["min"] / 1000,
                "max_mwh": response["ranges"]["total_yearly_demand"]["max"] / 1000
            }
        }
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics-ranges-complete")
def get_complete_metrics_ranges(
    exclude_zero: bool = Query(False, description="Exclude zero values from min calculation"),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get comprehensive metrics ranges with units and descriptions for all admin levels.
    Returns a complete object with all metrics, their ranges for each admin level, units, and descriptions.
    Perfect for frontend legend generation and metric understanding.
    
    Query parameters:
    - exclude_zero: Exclude zero values from min calculation (default: false)
    """
    try:
        # Define all admin levels
        admin_levels = ['region', 'department', 'arrondissement', 'commune']
        
        # Build min calculation clause
        min_clause = "MIN" if not exclude_zero else "MIN(NULLIF"
        min_suffix = "" if not exclude_zero else ", 0))"
        
        # Get ranges for each admin level
        ranges_by_level = {}
        
        for level in admin_levels:
            query = f"""
            SELECT 
                -- Basic building metrics
                {min_clause}(bs.total_buildings){min_suffix} as min_total_buildings,
                MAX(bs.total_buildings) as max_total_buildings,
                {min_clause}(bs.electrified_buildings){min_suffix} as min_electrified_buildings,
                MAX(bs.electrified_buildings) as max_electrified_buildings,
                {min_clause}(bs.unelectrified_buildings){min_suffix} as min_unelectrified_buildings,
                MAX(bs.unelectrified_buildings) as max_unelectrified_buildings,
                
                -- Electrification rates
                {min_clause}(bs.electrification_rate){min_suffix} as min_electrification_rate,
                MAX(bs.electrification_rate) as max_electrification_rate,
                
                -- High confidence rates
                {min_clause}(bs.high_confidence_rate_50){min_suffix} as min_high_confidence_rate_50,
                MAX(bs.high_confidence_rate_50) as max_high_confidence_rate_50,
                {min_clause}(bs.high_confidence_rate_60){min_suffix} as min_high_confidence_rate_60,
                MAX(bs.high_confidence_rate_60) as max_high_confidence_rate_60,
                {min_clause}(bs.high_confidence_rate_70){min_suffix} as min_high_confidence_rate_70,
                MAX(bs.high_confidence_rate_70) as max_high_confidence_rate_70,
                {min_clause}(bs.high_confidence_rate_80){min_suffix} as min_high_confidence_rate_80,
                MAX(bs.high_confidence_rate_80) as max_high_confidence_rate_80,
                {min_clause}(bs.high_confidence_rate_85){min_suffix} as min_high_confidence_rate_85,
                MAX(bs.high_confidence_rate_85) as max_high_confidence_rate_85,
                {min_clause}(bs.high_confidence_rate_90){min_suffix} as min_high_confidence_rate_90,
                MAX(bs.high_confidence_rate_90) as max_high_confidence_rate_90,
                
                -- Energy consumption and demand
                {min_clause}(bs.avg_consumption_kwh_month){min_suffix} as min_avg_consumption_kwh_month,
                MAX(bs.avg_consumption_kwh_month) as max_avg_consumption_kwh_month,
                {min_clause}(bs.avg_energy_demand_kwh_year){min_suffix} as min_avg_energy_demand_kwh_year,
                MAX(bs.avg_energy_demand_kwh_year) as max_avg_energy_demand_kwh_year,
                
                -- Calculated total consumption and demand
                {min_clause}(bs.total_buildings * bs.avg_consumption_kwh_month){min_suffix} as min_total_monthly_consumption,
                MAX(bs.total_buildings * bs.avg_consumption_kwh_month) as max_total_monthly_consumption,
                {min_clause}(bs.total_buildings * bs.avg_energy_demand_kwh_year){min_suffix} as min_total_yearly_demand,
                MAX(bs.total_buildings * bs.avg_energy_demand_kwh_year) as max_total_yearly_demand
            FROM 
                building_statistics bs
            JOIN 
                administrative_boundaries ab ON bs.admin_id = ab.id
            WHERE ab.level = :admin_level
            """
            
            result = db.execute(text(query), {"admin_level": level}).fetchone()
            
            if result:
                ranges_by_level[level] = {
                    "total_buildings": {
                        "min": float(result[0]) if result[0] is not None else 0,
                        "max": float(result[1]) if result[1] is not None else 0
                    },
                    "electrified_buildings": {
                        "min": float(result[2]) if result[2] is not None else 0,
                        "max": float(result[3]) if result[3] is not None else 0
                    },
                    "unelectrified_buildings": {
                        "min": float(result[4]) if result[4] is not None else 0,
                        "max": float(result[5]) if result[5] is not None else 0
                    },
                    "electrification_rate": {
                        "min": float(result[6]) if result[6] is not None else 0,
                        "max": float(result[7]) if result[7] is not None else 100
                    },
                    "high_confidence_rate_50": {
                        "min": float(result[8]) if result[8] is not None else 0,
                        "max": float(result[9]) if result[9] is not None else 100
                    },
                    "high_confidence_rate_60": {
                        "min": float(result[10]) if result[10] is not None else 0,
                        "max": float(result[11]) if result[11] is not None else 100
                    },
                    "high_confidence_rate_70": {
                        "min": float(result[12]) if result[12] is not None else 0,
                        "max": float(result[13]) if result[13] is not None else 100
                    },
                    "high_confidence_rate_80": {
                        "min": float(result[14]) if result[14] is not None else 0,
                        "max": float(result[15]) if result[15] is not None else 100
                    },
                    "high_confidence_rate_85": {
                        "min": float(result[16]) if result[16] is not None else 0,
                        "max": float(result[17]) if result[17] is not None else 100
                    },
                    "high_confidence_rate_90": {
                        "min": float(result[18]) if result[18] is not None else 0,
                        "max": float(result[19]) if result[19] is not None else 100
                    },
                    "avg_consumption_kwh_month": {
                        "min": float(result[20]) if result[20] is not None else 0,
                        "max": float(result[21]) if result[21] is not None else 0
                    },
                    "avg_energy_demand_kwh_year": {
                        "min": float(result[22]) if result[22] is not None else 0,
                        "max": float(result[23]) if result[23] is not None else 0
                    },
                    "total_monthly_consumption": {
                        "min": float(result[24]) if result[24] is not None else 0,
                        "max": float(result[25]) if result[25] is not None else 0
                    },
                    "total_yearly_demand": {
                        "min": float(result[26]) if result[26] is not None else 0,
                        "max": float(result[27]) if result[27] is not None else 0
                    }
                }
        
        # Define comprehensive metrics information
        metrics_info = {
            "total_buildings": {
                "unit": "buildings",
                "display_unit": "buildings",
                "description": "Total number of buildings in the administrative area",
                "category": "building_counts",
                "visualization_type": "density",
                "color_scheme": "greens",
                "ranges": {}
            },
            "electrified_buildings": {
                "unit": "buildings",
                "display_unit": "buildings", 
                "description": "Number of buildings with electricity access",
                "category": "building_counts",
                "visualization_type": "density",
                "color_scheme": "blues",
                "ranges": {}
            },
            "unelectrified_buildings": {
                "unit": "buildings",
                "display_unit": "buildings",
                "description": "Number of buildings without electricity access",
                "category": "building_counts", 
                "visualization_type": "density",
                "color_scheme": "reds",
                "ranges": {}
            },
            "electrification_rate": {
                "unit": "%",
                "display_unit": "%",
                "description": "Percentage of buildings with electricity access",
                "category": "rates",
                "visualization_type": "choropleth",
                "color_scheme": "red_yellow_green",
                "ranges": {}
            },
            "high_confidence_rate_50": {
                "unit": "%",
                "display_unit": "%",
                "description": "Percentage of buildings with >50% confidence of electrification",
                "category": "confidence_rates",
                "visualization_type": "choropleth", 
                "color_scheme": "red_yellow_green",
                "ranges": {}
            },
            "high_confidence_rate_60": {
                "unit": "%",
                "display_unit": "%",
                "description": "Percentage of buildings with >60% confidence of electrification",
                "category": "confidence_rates",
                "visualization_type": "choropleth",
                "color_scheme": "red_yellow_green", 
                "ranges": {}
            },
            "high_confidence_rate_70": {
                "unit": "%",
                "display_unit": "%",
                "description": "Percentage of buildings with >70% confidence of electrification",
                "category": "confidence_rates",
                "visualization_type": "choropleth",
                "color_scheme": "red_yellow_green",
                "ranges": {}
            },
            "high_confidence_rate_80": {
                "unit": "%", 
                "display_unit": "%",
                "description": "Percentage of buildings with >80% confidence of electrification",
                "category": "confidence_rates",
                "visualization_type": "choropleth",
                "color_scheme": "red_yellow_green",
                "ranges": {}
            },
            "high_confidence_rate_85": {
                "unit": "%",
                "display_unit": "%", 
                "description": "Percentage of buildings with >85% confidence of electrification",
                "category": "confidence_rates",
                "visualization_type": "choropleth",
                "color_scheme": "red_yellow_green",
                "ranges": {}
            },
            "high_confidence_rate_90": {
                "unit": "%",
                "display_unit": "%",
                "description": "Percentage of buildings with >90% confidence of electrification",
                "category": "confidence_rates", 
                "visualization_type": "choropleth",
                "color_scheme": "red_yellow_green",
                "ranges": {}
            },
            "avg_consumption_kwh_month": {
                "unit": "kWh/month",
                "display_unit": "kWh/month",
                "description": "Average monthly electricity consumption per building",
                "category": "energy_metrics",
                "visualization_type": "choropleth",
                "color_scheme": "blue_red",
                "alternative_units": {
                    "mwh_month": {"factor": 0.001, "unit": "MWh/month"},
                    "gwh_month": {"factor": 0.000001, "unit": "GWh/month"}
                },
                "ranges": {}
            },
            "avg_energy_demand_kwh_year": {
                "unit": "kWh/year",
                "display_unit": "kWh/year", 
                "description": "Average yearly electricity demand per building",
                "category": "energy_metrics",
                "visualization_type": "choropleth",
                "color_scheme": "blue_red",
                "alternative_units": {
                    "mwh_year": {"factor": 0.001, "unit": "MWh/year"},
                    "gwh_year": {"factor": 0.000001, "unit": "GWh/year"}
                },
                "ranges": {}
            },
            "total_monthly_consumption": {
                "unit": "kWh/month",
                "display_unit": "adaptive",
                "description": "Total monthly electricity consumption for all buildings in the area",
                "category": "energy_totals",
                "visualization_type": "choropleth",
                "color_scheme": "blues",
                "adaptive_units": [
                    {"threshold": 1000000000, "factor": 0.000000001, "unit": "TWh/month"},
                    {"threshold": 1000000, "factor": 0.000001, "unit": "GWh/month"},
                    {"threshold": 1000, "factor": 0.001, "unit": "MWh/month"},
                    {"threshold": 0, "factor": 1, "unit": "kWh/month"}
                ],
                "ranges": {}
            },
            "total_yearly_demand": {
                "unit": "kWh/year",
                "display_unit": "adaptive",
                "description": "Total yearly electricity demand for all buildings in the area", 
                "category": "energy_totals",
                "visualization_type": "choropleth",
                "color_scheme": "purples",
                "adaptive_units": [
                    {"threshold": 1000000000, "factor": 0.000000001, "unit": "TWh/year"},
                    {"threshold": 1000000, "factor": 0.000001, "unit": "GWh/year"},
                    {"threshold": 1000, "factor": 0.001, "unit": "MWh/year"},
                    {"threshold": 0, "factor": 1, "unit": "kWh/year"}
                ],
                "ranges": {}
            }
        }
        
        # Populate ranges for each metric
        for metric_key in metrics_info.keys():
            for level in admin_levels:
                if level in ranges_by_level and metric_key in ranges_by_level[level]:
                    metrics_info[metric_key]["ranges"][level] = ranges_by_level[level][metric_key]
        
        # Construct final response
        response = {
            "timestamp": datetime.now().isoformat(),
            "exclude_zero_from_min": exclude_zero,
            "admin_levels": admin_levels,
            "metrics": metrics_info,
            "summary": {
                "total_metrics": len(metrics_info),
                "categories": list(set([metric["category"] for metric in metrics_info.values()])),
                "admin_levels_covered": admin_levels,
                "visualization_types": list(set([metric["visualization_type"] for metric in metrics_info.values()]))
            }
        }
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/{admin_level}/{admin_name}", response_model=schemas.metrics.AdminMetricsResponse)
def get_admin_metrics(
    admin_level: str = Path(..., description="Administrative level (region, department, arrondissement, commune)"),
    admin_name: str = Path(..., description="Name of the administrative area"),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get metrics for any administrative level by name.
    Returns detailed statistics for the specified administrative area.
    """
    # Validate admin level
    valid_levels = ["region", "department", "arrondissement", "commune"]
    if admin_level not in valid_levels:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid administrative level. Must be one of: {', '.join(valid_levels)}"
        )

    try:
        # Get area statistics
        stats_query = """
        SELECT 
            bs.total_buildings,
            bs.electrified_buildings,
            bs.unelectrified_buildings,
            bs.electrification_rate,
            bs.high_confidence_rate_50,
            bs.high_confidence_rate_60,
            bs.high_confidence_rate_70,
            bs.high_confidence_rate_80,
            bs.high_confidence_rate_85,
            bs.high_confidence_rate_90,
            bs.avg_consumption_kwh_month,
            bs.avg_energy_demand_kwh_year
        FROM 
            building_statistics bs
        JOIN 
            administrative_boundaries ab ON bs.admin_id = ab.id
        WHERE 
            ab.level = :admin_level AND
            ab.name = :admin_name
        """
        
        stats_result = db.execute(
            text(stats_query), 
            {"admin_level": admin_level, "admin_name": admin_name}
        ).fetchone()
        
        if not stats_result:
            raise HTTPException(
                status_code=404, 
                detail=f"{admin_level.title()} '{admin_name}' not found"
            )
        
        # Get child areas
        # For commune level, we won't have children
        if admin_level != "commune":
            children_query = """
            SELECT 
                ab.name,
                bs.electrification_rate,
                bs.high_confidence_rate_90,
                bs.total_buildings
            FROM 
                building_statistics bs
            JOIN 
                administrative_boundaries ab ON bs.admin_id = ab.id
            JOIN 
                administrative_boundaries parent ON ab.parent_id = parent.id
            WHERE 
                parent.level = :parent_level AND
                parent.name = :parent_name AND
                ab.level = :child_level
            ORDER BY 
                bs.electrification_rate DESC
            """
            
            # Define child level based on current level
            level_hierarchy = {
                "region": "department",
                "department": "arrondissement",
                "arrondissement": "commune"
            }
            
            child_level = level_hierarchy.get(admin_level)
            
            children_result = db.execute(
                text(children_query), 
                {
                    "parent_level": admin_level,
                    "parent_name": admin_name,
                    "child_level": child_level
                }
            ).fetchall()
            
            children = [
                {
                    "name": row[0],
                    "electrification_rate": float(row[1]),
                    "high_confidence_rate": float(row[2]),
                    "total_buildings": int(row[3])
                }
                for row in children_result
            ]
        else:
            children = []
        
        # Construct the response
        response = {
            "timestamp": datetime.now().isoformat(),
            "admin_level": admin_level,
            "admin_name": admin_name,
            "statistics": {
                "total_buildings": int(stats_result[0]),
                "electrified_buildings": int(stats_result[1]),
                "unelectrified_buildings": int(stats_result[2]),
                "electrification_rate": float(stats_result[3]),
                "high_confidence_rates": {
                    "50_percent": float(stats_result[4]),
                    "60_percent": float(stats_result[5]),
                    "70_percent": float(stats_result[6]),
                    "80_percent": float(stats_result[7]),
                    "85_percent": float(stats_result[8]),
                    "90_percent": float(stats_result[9])
                },
                "avg_consumption_kwh_month": float(stats_result[10]),
                "avg_energy_demand_kwh_year": float(stats_result[11])
            },
            "children": children,
            "confidence_analysis": {
                "confidence_rate_gap": float(stats_result[3]) - float(stats_result[9]),
                "confidence_rate_gradient": [
                    {"threshold": "50%", "gap": float(stats_result[3]) - float(stats_result[4])},
                    {"threshold": "60%", "gap": float(stats_result[3]) - float(stats_result[5])},
                    {"threshold": "70%", "gap": float(stats_result[3]) - float(stats_result[6])},
                    {"threshold": "80%", "gap": float(stats_result[3]) - float(stats_result[7])},
                    {"threshold": "85%", "gap": float(stats_result[3]) - float(stats_result[8])},
                    {"threshold": "90%", "gap": float(stats_result[3]) - float(stats_result[9])}
                ]
            }
        }
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 