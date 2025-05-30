# Energy Model Metrics API

This API provides comprehensive metrics and analytics for the energy grid model, including national and regional electrification rates, high-confidence statistics, and planning insights.

## Setup and Installation

1. Ensure you have Python 3.7+ installed
2. Install the required packages:
   ```
   pip install flask flask-cors psycopg2-binary
   ```
3. Set environment variables if needed (or defaults will be used):
   - `DB_NAME` (default: energy_model)
   - `DB_USER` (default: postgres)
   - `DB_PASSWORD` (default: postgres)
   - `DB_HOST` (default: localhost)
   - `DB_PORT` (default: 5432)
   - `PORT` (API server port, default: 5000)

4. Start the API server:
   ```
   ./metrics_api.py
   ```

## API Endpoints

### 1. National Metrics

**Endpoint:** `GET /api/metrics/national`

Returns comprehensive statistics for the entire country, including:
- Overall electrification rate
- High-confidence electrification rates at multiple thresholds (50%, 60%, 70%, 80%, 85%, 90%)
- Top and least electrified regions
- Regions with highest confidence gaps
- Energy planning estimates

**Example response:**
```json
{
  "timestamp": "2023-07-20T14:30:45.123456",
  "national_statistics": {
    "total_buildings": 1250000,
    "electrified_buildings": 875000,
    "unelectrified_buildings": 375000,
    "electrification_rate": 70.0,
    "high_confidence_rates": {
      "50_percent": 65.2,
      "60_percent": 60.8,
      "70_percent": 55.3,
      "80_percent": 50.1,
      "85_percent": 47.5,
      "90_percent": 43.2
    },
    "avg_consumption_kwh_month": 25.5,
    "avg_energy_demand_kwh_year": 350.2
  },
  "geographic_insights": {
    "top_electrified_regions": [
      { "name": "Dakar", "electrification_rate": 95.2, "total_buildings": 320000 },
      { "name": "Saint-Louis", "electrification_rate": 82.3, "total_buildings": 85000 },
      { "name": "Thiès", "electrification_rate": 78.5, "total_buildings": 120000 }
    ],
    "least_electrified_regions": [
      { "name": "Kédougou", "electrification_rate": 35.2, "total_buildings": 25000 },
      { "name": "Matam", "electrification_rate": 42.3, "total_buildings": 35000 },
      { "name": "Kolda", "electrification_rate": 45.7, "total_buildings": 45000 }
    ],
    "highest_confidence_gap_regions": [
      { "name": "Tambacounda", "electrification_rate": 62.3, "high_confidence_rate": 32.1, "gap": 30.2 },
      { "name": "Kaffrine", "electrification_rate": 58.7, "high_confidence_rate": 30.4, "gap": 28.3 },
      { "name": "Sédhiou", "electrification_rate": 51.2, "high_confidence_rate": 25.8, "gap": 25.4 }
    ]
  },
  "confidence_analysis": {
    "confidence_rate_gap": 26.8,
    "confidence_rate_gradient": [
      { "threshold": "50%", "gap": 4.8 },
      { "threshold": "60%", "gap": 9.2 },
      { "threshold": "70%", "gap": 14.7 },
      { "threshold": "80%", "gap": 19.9 },
      { "threshold": "85%", "gap": 22.5 },
      { "threshold": "90%", "gap": 26.8 }
    ]
  },
  "energy_planning": {
    "total_estimated_monthly_consumption": 22312500,
    "total_estimated_annual_demand": 437750000,
    "unmet_annual_demand": 131325000
  }
}
```

### 2. Region Metrics

**Endpoint:** `GET /api/metrics/region/{region_name}`

Returns detailed statistics for a specific region, including:
- Region-specific electrification rates
- High-confidence rates at multiple thresholds
- List of departments within the region and their statistics
- Confidence gap analysis for the region

**Example usage:** `/api/metrics/region/Dakar`

### 3. Priority Zones

**Endpoint:** `GET /api/metrics/priority-zones`

Returns areas that should be prioritized for electrification planning, including:
- Areas with low electrification but high building density
- Areas with high confidence gaps (verification priorities)
- Areas with high unmet energy demand

This endpoint is particularly useful for planning field verification visits and new electrification projects.

### 4. All Regions List

**Endpoint:** `GET /api/metrics/regions`

Returns a list of all regions with basic statistics. Useful for building dashboards and selector components.

## Integration with Frontend

To integrate with your existing visualization:

1. Add fetch calls to these endpoints from your frontend code
2. Create visualizations like:
   - Bar charts comparing electrification rates across confidence thresholds
   - Maps showing priority zones
   - Dashboards with filterable regional statistics

## Security Considerations

This API does not include authentication. If deployed to production, consider adding:
- API key validation
- Rate limiting
- HTTPS encryption

## Further Development

Potential extensions to this API:
- Time-series analysis of electrification progress
- Predictive models for future electrification needs
- Cost estimates for closing electrification gaps 