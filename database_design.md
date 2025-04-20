# Energy Database Design (PostgreSQL + PostGIS)

## Overview

This document outlines the database schema design for storing country-level energy system data for a specific year. The chosen platform is PostgreSQL with the PostGIS extension to leverage its robust relational and geospatial capabilities.

## Core Requirements

*   Store data for a specific year and country.
*   Manage geospatial information for buildings, grid lines, power plants, water resources.
*   Store energy demand/access per building.
*   Store grid line transmission characteristics.
*   Store power plant details.
*   Store solar radiation data.
*   Store water resource information.
*   The system must be scalable, robust, and performant.

## Design Considerations

*   **Geospatial Data:** PostGIS `geometry` types will be used for storing spatial features (points, lines, polygons). Spatial indexes (e.g., GiST) will be crucial for performance.
*   **Year Specificity:** Data related to a specific year (like demand) will include a `year` column or be managed through partitioning or separate schemas if data volume per year becomes extremely large. For simplicity, this initial design uses a `year` column.
*   **Country Specificity:** While the data is *for* a country, the schema doesn't explicitly enforce *only* one country per database instance. Filtering by a country identifier or deploying separate instances per country would handle this. This design assumes a single country focus per deployment.
*   **Units:** Consistent units must be defined and potentially stored (e.g., in metadata tables or comments) for energy (kWh, MWh), power (kW, MW), distance (meters), etc.
*   **Data Sources:** Add columns to track the source and acquisition date/time for each piece of data for provenance.

## Schema Definition

---

**1. `buildings_energy`**

Stores information about individual buildings, including their footprint and energy characteristics.

| Column Name         | Data Type                     | Description                                      | Constraints/Notes             |
| :------------------ | :---------------------------- | :----------------------------------------------- | :---------------------------- |
| `building_id`       | `BIGSERIAL`                   | Unique identifier for the building               | PRIMARY KEY                   |
| `footprint`         | `geometry(Polygon, SRID)`     | Geographic footprint of the building             | SRID = e.g., 4326 (WGS 84)    |
| `year`              | `INTEGER`                     | The year this data pertains to                   | Not Null                      |
| `energy_demand_kwh` | `NUMERIC`                     | Estimated/Measured annual energy demand in kWh |                               |
| `has_access`        | `BOOLEAN`                     | Flag indicating if the building has grid access  |                               |
| `building_type`     | `VARCHAR(50)`                 | e.g., Residential, Commercial, Industrial      | Optional                      |
| `data_source`       | `VARCHAR(100)`                | Source of the building/demand data             |                               |
| `last_updated`      | `TIMESTAMP WITH TIME ZONE`    | When the record was last updated                 | DEFAULT `CURRENT_TIMESTAMP` |
| `grid_node_id`      | `BIGINT`                      | FK to the nearest/connecting grid node           | FOREIGN KEY (`grid_nodes`)    |

**Spatial Index:** `CREATE INDEX idx_buildings_geom ON buildings USING GIST (footprint);`
**Attribute Index:** `CREATE INDEX idx_buildings_year ON buildings (year);`

---

**2. `grid_nodes`**

Represents connection points or substations in the electricity grid.

| Column Name   | Data Type                 | Description                                      | Constraints/Notes          |
| :------------ | :------------------------ | :----------------------------------------------- | :------------------------- |
| `node_id`     | `BIGSERIAL`               | Unique identifier for the grid node              | PRIMARY KEY                |
| `location`    | `geometry(Point, SRID)`   | Geographic location of the node                  | SRID = e.g., 4326 (WGS 84) |
| `node_type`   | `VARCHAR(50)`             | e.g., Substation, Transformer, Junction          |                            |
| `voltage_kv`  | `NUMERIC`                 | Voltage level at the node (if applicable)      |                            |
| `data_source` | `VARCHAR(100)`            | Source of the node data                          |                            |
| `last_updated` | `TIMESTAMP WITH TIME ZONE` | When the record was last updated                 | DEFAULT `CURRENT_TIMESTAMP`|

**Spatial Index:** `CREATE INDEX idx_grid_nodes_geom ON grid_nodes USING GIST (location);`

---

**3. `grid_lines`**

Stores information about transmission and distribution lines.

| Column Name      | Data Type                    | Description                                       | Constraints/Notes                             |
| :--------------- | :--------------------------- | :------------------------------------------------ | :-------------------------------------------- |
| `line_id`        | `BIGSERIAL`                  | Unique identifier for the grid line               | PRIMARY KEY                                   |
| `path`           | `geometry(LineString, SRID)` | Geographic path of the line                       | SRID = e.g., 4326 (WGS 84)                    |
| `year`           | `INTEGER`                    | The year this data pertains to                    | Not Null                                      |
| `voltage_kv`     | `NUMERIC`                    | Voltage level of the line                         |                                               |
| `capacity_mva`   | `NUMERIC`                    | Transmission capacity in MVA                      |                                               |
| `line_type`      | `VARCHAR(50)`                | e.g., Transmission, Distribution, Overhead, Underground |                                               |
| `start_node_id`  | `BIGINT`                     | FK to the starting grid node                      | FOREIGN KEY (`grid_nodes`)                    |
| `end_node_id`    | `BIGINT`                     | FK to the ending grid node                        | FOREIGN KEY (`grid_nodes`)                    |
| `data_source`    | `VARCHAR(100)`               | Source of the line data                           |                                               |
| `last_updated`   | `TIMESTAMP WITH TIME ZONE`   | When the record was last updated                  | DEFAULT `CURRENT_TIMESTAMP`                   |

**Spatial Index:** `CREATE INDEX idx_grid_lines_geom ON grid_lines USING GIST (path);`
**Attribute Index:** `CREATE INDEX idx_grid_lines_year ON grid_lines (year);`

---

**4. `power_plants`**

Stores information about power generation facilities.

| Column Name      | Data Type                 | Description                                      | Constraints/Notes                             |
| :--------------- | :------------------------ | :----------------------------------------------- | :-------------------------------------------- |
| `plant_id`       | `BIGSERIAL`               | Unique identifier for the power plant            | PRIMARY KEY                                   |
| `location`       | `geometry(Point, SRID)`   | Geographic location of the plant                 | SRID = e.g., 4326 (WGS 84)                    |
| `plant_name`     | `VARCHAR(255)`            | Name of the power plant                          |                                               |
| `year`           | `INTEGER`                 | The year this data pertains to                   | Not Null                                      |
| `plant_type`     | `VARCHAR(50)`             | e.g., Coal, Gas, Hydro, Solar, Wind, Nuclear   |                                               |
| `capacity_mw`    | `NUMERIC`                 | Installed capacity in MW                         |                                               |
| `annual_gen_gwh` | `NUMERIC`                 | Estimated/Actual annual generation in GWh      | Optional                                      |
| `grid_node_id`   | `BIGINT`                  | FK to the connecting grid node                   | FOREIGN KEY (`grid_nodes`) Optional           |
| `data_source`    | `VARCHAR(100)`            | Source of the plant data                         |                                               |
| `last_updated`   | `TIMESTAMP WITH TIME ZONE`| When the record was last updated                 | DEFAULT `CURRENT_TIMESTAMP`                   |

**Spatial Index:** `CREATE INDEX idx_power_plants_geom ON power_plants USING GIST (location);`
**Attribute Index:** `CREATE INDEX idx_power_plants_year ON power_plants (year);`

---

**5. `solar_radiation`**

Stores solar radiation data, potentially as a raster or aggregated to administrative zones. Storing raw raster data directly in PostGIS is possible (`raster` type) but can be complex. An alternative is storing data aggregated by region/grid cell. This example assumes regional aggregation.

| Column Name         | Data Type                 | Description                                         | Constraints/Notes                          |
| :------------------ | :------------------------ | :-------------------------------------------------- | :----------------------------------------- |
| `radiation_id`      | `BIGSERIAL`               | Unique identifier                                   | PRIMARY KEY                                |
| `region_geometry`   | `geometry(Polygon, SRID)` | Geographic area this data applies to (e.g., grid cell, admin area) | SRID = e.g., 4326 (WGS 84)         |
| `year`              | `INTEGER`                 | The year this data pertains to                      | Not Null                                   |
| `avg_ghi_kwh_m2_yr` | `NUMERIC`                 | Average Global Horizontal Irradiance (kWh/m²/year)  |                                            |
| `avg_dni_kwh_m2_yr` | `NUMERIC`                 | Average Direct Normal Irradiance (kWh/m²/year)    |                                            |
| `data_source`       | `VARCHAR(100)`            | Source of the radiation data                        |                                            |
| `last_updated`      | `TIMESTAMP WITH TIME ZONE`| When the record was last updated                    | DEFAULT `CURRENT_TIMESTAMP`                |

**Spatial Index:** `CREATE INDEX idx_solar_radiation_geom ON solar_radiation USING GIST (region_geometry);`
**Attribute Index:** `CREATE INDEX idx_solar_radiation_year ON solar_radiation (year);`

---

**6. `water_resources`**

Stores information about water bodies relevant to energy (e.g., for hydro power, cooling).

| Column Name     | Data Type                     | Description                                             | Constraints/Notes                          |
| :-------------- | :---------------------------- | :------------------------------------------------------ | :----------------------------------------- |
| `resource_id`   | `BIGSERIAL`                   | Unique identifier                                       | PRIMARY KEY                                |
| `geometry`      | `geometry(Geometry, SRID)`    | Geographic representation (Point, LineString, Polygon)  | SRID = e.g., 4326 (WGS 84)                 |
| `resource_type` | `VARCHAR(50)`                 | e.g., River, Lake, Reservoir                          |                                            |
| `name`          | `VARCHAR(255)`                | Name of the water resource                              | Optional                                   |
| `flow_rate_m3_s`| `NUMERIC`                     | Average flow rate (for rivers)                          | Optional                                   |
| `volume_mcm`    | `NUMERIC`                     | Volume (for lakes/reservoirs) in million cubic meters | Optional                                   |
| `data_source`   | `VARCHAR(100)`                | Source of the water data                                |                                            |
| `last_updated`  | `TIMESTAMP WITH TIME ZONE`    | When the record was last updated                        | DEFAULT `CURRENT_TIMESTAMP`                |

**Spatial Index:** `CREATE INDEX idx_water_resources_geom ON water_resources USING GIST (geometry);`

---

## Future Considerations

*   **Time Series Data:** If data becomes more granular than annual (e.g., hourly demand), consider using TimescaleDB or implementing table partitioning on a timestamp column.
*   **Raster Data:** For high-resolution solar or weather data, investigate the PostGIS Raster extension or store raster data externally (e.g., in cloud storage) with references in the database.
*   **Network Topology:** For advanced grid analysis, graph database features (potentially within PostgreSQL using extensions like `pgrouting` or Age) or dedicated graph databases could be explored.
*   **Metadata Tables:** Add tables for units, data source details, SRID information, etc.
*   **User Roles/Permissions:** Implement appropriate security measures. 