# Administrative Statistics Module

This module enables visualization of building statistics aggregated at different administrative levels (region, department, arrondissement, commune) in Senegal.

## Overview

The administrative statistics module provides:

1. **Hierarchical Visualization**: View statistics at different administrative levels from the highest (region) to the lowest (commune)
2. **Multiple Statistics**: Visualize different metrics including electrification rate, building density, and energy consumption
3. **Color-Coded Maps**: Each administrative area is colored based on the selected statistic, providing an intuitive visualization
4. **Detailed Popup Information**: Click on any area to see detailed statistics

## Setup Instructions

### 1. Import Administrative Boundaries

The system uses an API to fetch GeoJSON data for each administrative level. Run:

```bash
./import_admin_stats.sh
```

This will:
- Download boundary data from the APIs specified in `admin_boundaries.json`
- Import boundaries into the database with proper hierarchy
- Calculate statistics for each area
- Create views for efficient vector tile rendering
- Restart the Martin tile server

### 2. Data Structure

The module sets up these key database components:

#### Tables
- **administrative_boundaries**: Stores boundary geometries and hierarchy information
- **building_statistics**: Stores aggregated statistics for each administrative area

#### Views
- **admin_statistics_view**: Combines boundaries and statistics for querying
- **admin_statistics_materialized**: Materialized view for better performance with tile serving

## Using the Interface

The web application provides controls for interacting with administrative statistics:

1. **Enable Administrative Statistics**: Check the "Show Administrative Statistics" checkbox
2. **Select Administrative Level**:
   - Region (Level 1): Highest administrative division
   - Department (Level 2): Sub-division of regions
   - Arrondissement (Level 3): Sub-division of departments
   - Commune (Level 4): Lowest administrative division

3. **Select Statistic Type**:
   - **Electrification Rate**: Percentage of buildings with electricity (0-100%)
   - **Building Density**: Number of buildings in the area
   - **Average Monthly Consumption**: Average electricity consumption (kWh/month)
   - **Average Energy Demand**: Average annual energy demand (kWh/year)

## Technical Implementation

### Data Flow

1. Administrative boundaries are fetched from external APIs
2. Boundaries are stored in PostGIS with proper parent-child relationships
3. For each commune, buildings are counted and statistics are calculated
4. Statistics are aggregated upward through the hierarchy
5. Martin serves vector tiles with these statistics
6. The web frontend renders these tiles with appropriate styling

### Calculation Methodology

Statistics are calculated as follows:

- **Total Buildings**: Count of all buildings within each area
- **Electrified Buildings**: Count of buildings with `predicted_electrified = 1`
- **Unelectrified Buildings**: Count of buildings with `predicted_electrified = 0` or null
- **Electrification Rate**: `(electrified_buildings / total_buildings) * 100`
- **Avg. Consumption**: Average of `consumption_kwh_month` for all buildings
- **Avg. Energy Demand**: Average of `energy_demand_kwh` for all buildings

### Dynamic Filtering

The Martin configuration includes filters to show appropriate detail at each zoom level:

- Zoom 0-6: Only regions are shown
- Zoom 7-8: Regions and departments
- Zoom 9-10: Regions, departments, and arrondissements
- Zoom 11+: All levels including communes

## Extending the Module

To add new statistics:

1. Add the new statistic column to `building_statistics` table
2. Update the calculation in `calculate_statistics()` in the import script
3. Add a new color scheme in the `colors` object in `admin_stats.js`
4. Add a new legend configuration in the `legends` object
5. Add the new option to the "Statistic Type" dropdown in `index.html`