# Database Schema Documentation

This document provides an overview of the database structure used in the Energy Model Backend, including tables, relationships, and key fields.

## Table of Contents

1. [Overview](#overview)
2. [Core Tables](#core-tables)
   - [buildings_energy](#buildings_energy)
   - [administrative_boundaries](#administrative_boundaries)
   - [building_statistics](#building_statistics)
3. [Grid Infrastructure](#grid-infrastructure)
   - [grid_nodes](#grid_nodes)
   - [grid_lines](#grid_lines)
   - [power_plants](#power_plants)
4. [Unelectrified Analysis](#unelectrified-analysis)
   - [unelectrified_buildings](#unelectrified_buildings)
   - [unelectrified_clusters](#unelectrified_clusters)
5. [Views and Materialized Views](#views-and-materialized-views)
   - [admin_statistics_view](#admin_statistics_view)
   - [admin_statistics_materialized](#admin_statistics_materialized)
6. [Entity Relationship Diagram](#entity-relationship-diagram)

## Overview

The database is designed to store and analyze energy-related data, including building electrification status, administrative boundaries, and grid infrastructure. It uses PostGIS for spatial operations and is optimized for both analytical queries and vector tile serving.

## Core Tables

### buildings_energy

This is the main table storing building data with energy information.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary key |
| geom | geometry(MultiPolygon,4326) | Polygon geometry of the building |
| area_in_meters | double precision | Area of the building in square meters |
| year | integer | Year of data collection |
| energy_demand_kwh | double precision | Annual energy demand in kWh |
| has_access | boolean | Whether the building has electricity access |
| building_type | varchar | Type of building (residential, commercial, etc.) |
| data_source | varchar | Source of the building data |
| grid_node_id | varchar | Reference to the grid node serving this building |
| origin_id | varchar | Original ID from the source dataset |
| predicted_prob | double precision | ML-predicted probability of electrification |
| predicted_electrified | integer | Binary prediction (1=electrified, 0=not) |
| consumption_kwh_month | double precision | Monthly electricity consumption in kWh |
| std_consumption_kwh_month | double precision | Standard deviation of monthly consumption |
| origin | text | Origin of the building data |
| created_at | timestamp | Creation timestamp |
| updated_at | timestamp | Last update timestamp |

**Indexes:**
- Primary Key: id
- Spatial index: geom
- Additional indexes on: year, has_access, building_type, grid_node_id, predicted_prob, predicted_electrified, consumption_kwh_month

### administrative_boundaries

Stores hierarchical administrative boundaries (regions, departments, arrondissements, communes).

| Column | Type | Description |
|--------|------|-------------|
| id | text | Primary key |
| name | text | Name of the administrative area |
| level | text | Level type (region, department, arrondissement, commune) |
| level_num | integer | Numeric level (1=region, 2=department, etc.) |
| parent_id | text | FK to parent administrative area |
| geom | geometry(MultiPolygon,4326) | Polygon geometry of the boundary |

**Indexes:**
- Primary Key: id
- Spatial index: geom
- Additional indexes on: level, parent_id

**Foreign Keys:**
- parent_id references administrative_boundaries(id)

### building_statistics

Aggregated statistics for administrative areas.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary key |
| admin_id | text | FK to administrative_boundaries |
| total_buildings | integer | Total number of buildings |
| electrified_buildings | integer | Number of electrified buildings |
| high_confidence_50 | integer | Buildings with ≥50% confidence of being electrified |
| high_confidence_60 | integer | Buildings with ≥60% confidence of being electrified |
| high_confidence_70 | integer | Buildings with ≥70% confidence of being electrified |
| high_confidence_80 | integer | Buildings with ≥80% confidence of being electrified |
| high_confidence_85 | integer | Buildings with ≥85% confidence of being electrified |
| high_confidence_90 | integer | Buildings with ≥90% confidence of being electrified |
| unelectrified_buildings | integer | Number of unelectrified buildings |
| electrification_rate | double precision | Percentage of buildings that are electrified |
| high_confidence_rate_50 | double precision | Percentage of buildings with ≥50% confidence |
| high_confidence_rate_60 | double precision | Percentage of buildings with ≥60% confidence |
| high_confidence_rate_70 | double precision | Percentage of buildings with ≥70% confidence |
| high_confidence_rate_80 | double precision | Percentage of buildings with ≥80% confidence |
| high_confidence_rate_85 | double precision | Percentage of buildings with ≥85% confidence |
| high_confidence_rate_90 | double precision | Percentage of buildings with ≥90% confidence |
| avg_consumption_kwh_month | double precision | Average monthly consumption in kWh |
| avg_energy_demand_kwh_year | double precision | Average annual energy demand in kWh |
| updated_at | timestamp | Last update timestamp |

**Indexes:**
- Primary Key: id
- Unique constraint on admin_id

**Foreign Keys:**
- admin_id references administrative_boundaries(id)

## Grid Infrastructure

### grid_nodes

Stores grid nodes (transformers, substations, etc.).

| Column | Type | Description |
|--------|------|-------------|
| node_id | bigint | Primary key |
| year | integer | Year of data validity |
| location | geometry(Point,4326) | Point geometry of the node |
| properties | jsonb | Additional properties in JSON format |

**Indexes:**
- Primary Key: node_id
- Spatial index: location
- Additional index on: year

### grid_lines

Stores grid lines (transmission, distribution lines).

| Column | Type | Description |
|--------|------|-------------|
| line_id | bigint | Primary key |
| year | integer | Year of data validity |
| path | geometry(LineString,4326) | LineString geometry of the grid line |
| properties | jsonb | Additional properties in JSON format |

**Indexes:**
- Primary Key: line_id
- Spatial index: path
- Additional index on: year

### power_plants

Stores power generation facilities.

| Column | Type | Description |
|--------|------|-------------|
| plant_id | bigint | Primary key |
| year | integer | Year of data validity |
| location | geometry(Point,4326) | Point geometry of the power plant |
| properties | jsonb | Additional properties in JSON format |

**Indexes:**
- Primary Key: plant_id
- Spatial index: location
- Additional index on: year

## Unelectrified Analysis

### unelectrified_buildings

Detailed information about buildings without electricity access.

| Column | Type | Description |
|--------|------|-------------|
| id | integer | Primary key |
| origin | text | Origin of the building data |
| origin_id | text | Original ID from the source dataset |
| origin_origin_id | text | Original ID from upstream source |
| area_in_meters | double precision | Area of the building in square meters |
| n_bldgs_1km_away | integer | Number of buildings within 1km |
| lulc2023_built_area_n1 | double precision | Land use - built area within 1km |
| lulc2023_rangeland_n1 | double precision | Land use - rangeland within 1km |
| lulc2023_crops_n1 | double precision | Land use - crops within 1km |
| lulc2023_built_area_n11 | double precision | Land use - built area within 11km |
| lulc2023_rangeland_n11 | double precision | Land use - rangeland within 11km |
| lulc2023_crops_n11 | double precision | Land use - crops within 11km |
| ntl2023_n1 | double precision | Night time lights within 1km |
| ntl2023_n11 | double precision | Night time lights within 11km |
| ookla_fixed_20230101_avg_d_kbps | double precision | Fixed internet speed in kbps |
| ookla_fixed_20230101_devices | integer | Number of fixed internet devices |
| ookla_mobile_20230101_avg_d_kbps | double precision | Mobile internet speed in kbps |
| ookla_mobile_20230101_devices | integer | Number of mobile devices |
| predicted_prob | double precision | ML-predicted probability of electrification |
| predicted_electrified | integer | Binary prediction (1=electrified, 0=not) |
| consumption_kwh_month | double precision | Estimated monthly consumption if electrified |
| std_consumption_kwh_month | double precision | Standard deviation of consumption estimate |
| geom | geometry(Polygon,4326) | Polygon geometry of the building |

**Indexes:**
- Primary Key: id
- Spatial index: geom

### unelectrified_clusters

Clusters of unelectrified buildings for targeted interventions.

| Column | Type | Description |
|--------|------|-------------|
| cluster_id | integer | Primary key |
| year | integer | Year of data validity |
| area | geometry(Polygon,4326) | Polygon geometry of the cluster |
| properties | jsonb | Additional properties in JSON format |
| total_buildings | integer | Total buildings in the cluster |
| total_energy_kwh | real | Total estimated energy needed |
| avg_energy_kwh | real | Average energy need per building |

**Indexes:**
- Primary Key: cluster_id
- Spatial index: area
- Additional index on: year

## Views and Materialized Views

### admin_statistics_view

A view joining administrative boundaries with their statistics.

| Column | From Table | Description |
|--------|------------|-------------|
| id | administrative_boundaries | Primary key |
| name | administrative_boundaries | Name of the administrative area |
| level | administrative_boundaries | Level type |
| level_num | administrative_boundaries | Numeric level |
| parent_id | administrative_boundaries | FK to parent area |
| total_buildings | building_statistics | Total number of buildings |
| electrified_buildings | building_statistics | Number of electrified buildings |
| ... (other statistics columns) | building_statistics | Various statistics |
| geom | administrative_boundaries | Polygon geometry |

### admin_statistics_materialized

A materialized view of admin_statistics_view for better performance.

Contains the same structure as admin_statistics_view but stored as a materialized view for faster query performance, especially for vector tile serving.

## Entity Relationship Diagram

```
+----------------------+       +---------------------------+
| administrative_      |       | building_statistics       |
| boundaries           |       |                           |
|----------------------|       |---------------------------|
| id (PK)              |<------| admin_id (FK)             |
| name                 |       | total_buildings           |
| level                |       | electrified_buildings     |
| level_num            |       | ... (statistics)          |
| parent_id (self FK)  |       +---------------------------+
| geom                 |
+----------------------+
         ^
         | (Spatial)
         |
+----------------------+       +---------------------------+
| buildings_energy     |       | unelectrified_buildings   |
|----------------------|       |---------------------------|
| id (PK)              |       | id (PK)                   |
| geom                 |       | ... (attributes)          |
| ... (attributes)     |       | geom                      |
+----------------------+       +---------------------------+
         |
         | (Reference)
         v
+----------------------+       +---------------------------+
| grid_nodes           |       | grid_lines                |
|----------------------|       |---------------------------|
| node_id (PK)         |       | line_id (PK)              |
| year                 |       | year                      |
| location             |       | path                      |
| properties           |       | properties                |
+----------------------+       +---------------------------+
```

This diagram shows the main relationships between key tables in the database. Administrative boundaries have a hierarchical relationship with themselves (parent-child). Buildings are spatially contained within administrative boundaries. Grid nodes can be referenced by buildings. 