# Frontend Developer Guide

This document provides comprehensive guidance for frontend developers working with the Energy Model API. It covers how to make API requests, interpret responses, and effectively visualize the data.

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Buildings API](#buildings-api)
4. [Metrics API](#metrics-api)
5. [Vector Tiles Integration](#vector-tiles-integration)
6. [Data Visualization Guidelines](#data-visualization-guidelines)
7. [Best Practices](#best-practices)
8. [Examples](#examples)

## API Overview

The Energy Model API provides access to building data, energy statistics, and administrative boundaries for Senegal. It's built with FastAPI and follows RESTful principles. All responses are in JSON format.

Base URL: `http://localhost:8008/api/v1/`

## Authentication

Currently, the API doesn't require authentication for local development. If you're using a production deployment, authentication may be required - consult your project administrator.

## Buildings API

### List Buildings

Retrieve a paginated list of buildings with optional filtering.

```
GET /api/v1/buildings/
```

**Query Parameters:**
- `skip` (integer): Number of records to skip (default: 0)
- `limit` (integer): Maximum number of records to return (default: 100)
- `year` (integer): Filter by year
- `has_access` (boolean): Filter by electrification status
- `building_type` (string): Filter by building type

**Example Request:**
```javascript
fetch('http://localhost:8008/api/v1/buildings/?limit=10&has_access=true')
  .then(response => response.json())
  .then(data => console.log(data));
```

**Response:**
```json
[
  {
    "id": 11600676,
    "geom": "MULTIPOLYGON(((-16.3314408535598 15.3244741633806, -16.3314508407051 15.3245030595542, -16.331481847825 15.3244929659771, -16.3314718606762 15.3244640698055, -16.3314408535598 15.3244741633806)))",
    "area_in_meters": 11.8865,
    "year": 2025,
    "energy_demand_kwh": 142.63849639892578,
    "has_access": true,
    "building_type": null,
    "data_source": "electrification_2025_model",
    "grid_node_id": null,
    "origin_id": "7C758MF9+QCV6",
    "predicted_prob": 0.7636574506759644,
    "predicted_electrified": 1,
    "consumption_kwh_month": 11.886541366577148,
    "std_consumption_kwh_month": 365.573974609375,
    "origin": "Google Open Buildings",
    "created_at": "2025-05-20T12:59:37.991283",
    "updated_at": "2025-05-20T12:59:37.991283"
  },
  // ... more buildings
]
```

### Buildings in Bounding Box

Retrieve buildings within a specified geographic area.

```
GET /api/v1/buildings/bbox
```

**Query Parameters:**
- `minx` (float): Minimum X coordinate (longitude)
- `miny` (float): Minimum Y coordinate (latitude)
- `maxx` (float): Maximum X coordinate (longitude)
- `maxy` (float): Maximum Y coordinate (latitude)
- `limit` (integer): Maximum number of records to return (default: 1000)

**Example Request:**
```javascript
fetch('http://localhost:8008/api/v1/buildings/bbox?minx=-17.5&miny=14.5&maxx=-17.4&maxy=14.6&limit=100')
  .then(response => response.json())
  .then(data => console.log(data));
```

### Building Statistics

Get aggregated statistics about buildings.

```
GET /api/v1/buildings/statistics
```

**Example Request:**
```javascript
fetch('http://localhost:8008/api/v1/buildings/statistics')
  .then(response => response.json())
  .then(data => console.log(data));
```

## Metrics API

The Metrics API provides high-level statistics and insights about electrification status across different administrative levels.

### National Metrics

Get comprehensive national-level electrification metrics, including statistics with various confidence thresholds.

```
GET /api/v1/metrics/national
```

**Example Request:**
```javascript
fetch('http://localhost:8008/api/v1/metrics/national')
  .then(response => response.json())
  .then(data => console.log(data));
```

**Response (sample):**
```json
{
  "timestamp": "2025-05-22T12:11:41.773611",
  "national_statistics": {
    "total_buildings": 6626182,
    "electrified_buildings": 6398140,
    "unelectrified_buildings": 228042,
    "electrification_rate": 96.55847062456178,
    "high_confidence_rates": {
      "50_percent": 96.55847062456178,
      "60_percent": 96.00178504001249,
      "70_percent": 94.44945822496274,
      "80_percent": 87.90609735742242,
      "85_percent": 84.196268680818,
      "90_percent": 81.58164083026999
    },
    "avg_consumption_kwh_month": 45.452261257594614,
    "avg_energy_demand_kwh_year": 545.4271350911355
  },
  "geographic_insights": {
    "top_electrified_regions": [
      // List of regions with highest electrification rates
    ],
    "least_electrified_regions": [
      // List of regions with lowest electrification rates
    ],
    "highest_confidence_gap_regions": [
      // Regions with largest gap between overall and high-confidence rates
    ]
  },
  "confidence_analysis": {
    "confidence_rate_gap": 14.976829794291788,
    "confidence_rate_gradient": [
      // Breakdown of confidence gaps at different thresholds
    ]
  },
  "energy_planning": {
    "total_estimated_monthly_consumption": 290809930.8426664,
    "total_estimated_annual_demand": 3614099464.8524504,
    "unmet_annual_demand": 124380294.74045272
  }
}
```

### Regions List

Get a list of all regions with basic electrification statistics.

```
GET /api/v1/metrics/regions
```

**Example Request:**
```javascript
fetch('http://localhost:8008/api/v1/metrics/regions')
  .then(response => response.json())
  .then(data => console.log(data));
```

### Region Detail

Get detailed metrics for a specific region including department-level breakdown.

```
GET /api/v1/metrics/region/{region_name}
```

**Path Parameters:**
- `region_name` (string): Name of the region (e.g., "Dakar", "Thiès")

**Example Request:**
```javascript
fetch('http://localhost:8008/api/v1/metrics/region/Dakar')
  .then(response => response.json())
  .then(data => console.log(data));
```

### Priority Zones

Identify priority areas for electrification efforts, verification, and high energy demand.

```
GET /api/v1/metrics/priority-zones
```

**Example Request:**
```javascript
fetch('http://localhost:8008/api/v1/metrics/priority-zones')
  .then(response => response.json())
  .then(data => console.log(data));
```

**Response Structure:**
- `electrification_priority_zones`: Areas with lowest electrification rates
- `verification_priority_zones`: Areas with large gaps between overall and high-confidence rates
- `high_demand_priority_zones`: Areas with highest unmet energy demand

### Uncertainty Analysis

Categorize communes based on their energy consumption estimation uncertainty.

```
GET /api/v1/metrics/uncertainty-analysis
```

**Example Request:**
```javascript
fetch('http://localhost:8008/api/v1/metrics/uncertainty-analysis')
  .then(response => response.json())
  .then(data => console.log(data));
```

**Response Structure:**
- `high_uncertainty_communes`: Communes with highest std_dev to mean ratio
- `medium_uncertainty_communes`: Communes with medium uncertainty
- `low_uncertainty_communes`: Communes with relatively lower uncertainty
- `statistics`: Overall statistics about the uncertainty distribution

## Vector Tiles Integration

The backend uses Martin to serve vector tiles from PostGIS. These can be integrated with MapLibre GL JS in your frontend.

### Accessing Vector Tiles

Vector tiles are available at:

```
http://localhost:3015/tiles/{layer_name}/{z}/{x}/{y}.pbf
```

Available layers:
- `buildings_energy`: All buildings with energy data
- `admin_statistics_materialized`: Administrative boundaries with statistics

### MapLibre Integration Example

```javascript
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

// Initialize map
const map = new maplibregl.Map({
  container: 'map',
  style: {
    version: 8,
    sources: {
      'osm-tiles': {
        type: 'raster',
        tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution: '© OpenStreetMap contributors'
      },
      'buildings': {
        type: 'vector',
        tiles: ['http://localhost:3015/tiles/buildings_energy/{z}/{x}/{y}.pbf'],
        minzoom: 10,
        maxzoom: 16
      },
      'admin-boundaries': {
        type: 'vector',
        tiles: ['http://localhost:3015/tiles/admin_statistics_materialized/{z}/{x}/{y}.pbf'],
        minzoom: 5,
        maxzoom: 12
      }
    },
    glyphs: "https://api.mapbox.com/fonts/v1/mapbox/{fontstack}/{range}.pbf?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw",
    layers: [
      {
        id: 'osm-tiles',
        type: 'raster',
        source: 'osm-tiles',
        minzoom: 0,
        maxzoom: 22
      },
      // Buildings layer
      {
        id: 'buildings-layer',
        type: 'fill',
        source: 'buildings',
        'source-layer': 'buildings_energy',
        paint: {
          'fill-color': [
            'case',
            ['==', ['get', 'has_access'], true], '#4CAF50', // Electrified
            '#F44336' // Unelectrified
          ],
          'fill-opacity': 0.8
        },
        minzoom: 13
      },
      // Administrative boundaries layer
      {
        id: 'admin-boundaries',
        type: 'fill',
        source: 'admin-boundaries',
        'source-layer': 'admin_statistics_materialized',
        paint: {
          'fill-color': [
            'interpolate',
            ['linear'],
            ['get', 'electrification_rate'],
            0, '#F44336',
            50, '#FFEB3B',
            100, '#4CAF50'
          ],
          'fill-opacity': 0.5,
          'fill-outline-color': '#000'
        },
        filter: ['==', ['get', 'level'], 'region']
      },
      // Admin boundary labels
      {
        id: 'admin-boundaries-labels',
        type: 'symbol',
        source: 'admin-boundaries',
        'source-layer': 'admin_statistics_materialized',
        layout: {
          'text-field': [
            'concat',
            ['get', 'name'], '\n',
            ['number-format', ['get', 'electrification_rate'], { 'maxFractionDigits': 1 }], '%'
          ],
          'text-font': ['Open Sans Regular', 'Arial Unicode MS Bold'],
          'text-size': 12,
          'text-anchor': 'center'
        },
        paint: {
          'text-color': '#000',
          'text-halo-color': '#fff',
          'text-halo-width': 1
        }
      }
    ]
  },
  center: [-15.3026, 14.7072], // Center on Senegal
  zoom: 6
});

// Add popup for buildings
map.on('click', 'buildings-layer', (e) => {
  const properties = e.features[0].properties;
  const electrified = properties.has_access ? 'Yes' : 'No';
  
  new maplibregl.Popup()
    .setLngLat(e.lngLat)
    .setHTML(`
      <h3>Building ${properties.id}</h3>
      <p>Electrified: ${electrified}</p>
      <p>Energy Demand: ${properties.energy_demand_kwh} kWh</p>
      <p>Monthly Consumption: ${properties.consumption_kwh_month} kWh</p>
    `)
    .addTo(map);
});

// Add layer controls
const toggleLayer = (layerId, visible) => {
  map.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none');
};

// Switch between admin levels
const updateAdminLevel = (level) => {
  map.setFilter('admin-boundaries', ['==', ['get', 'level'], level]);
  map.setFilter('admin-boundaries-labels', ['==', ['get', 'level'], level]);
};
```

## Data Visualization Guidelines

### Color Schemes

For electrification rates:
- High rates (80-100%): Green (#4CAF50 to #2E7D32)
- Medium rates (50-80%): Yellow to Orange (#FFEB3B to #FF9800)
- Low rates (0-50%): Orange to Red (#FF9800 to #F44336)

For uncertainty analysis:
- High uncertainty: Red (#F44336)
- Medium uncertainty: Orange (#FF9800)
- Low uncertainty: Yellow (#FFEB3B)

### Visualization Types

1. **Choropleth Maps**: Best for displaying rates across administrative boundaries
   - Electrification rates
   - High-confidence electrification rates
   - Building density

2. **Heat Maps**: Ideal for showing density of buildings
   - Unelectrified building clusters
   - Energy demand hotspots

3. **Point Maps**: For detailed building-level visualization
   - Individual buildings colored by electrification status
   - Grid infrastructure (nodes, lines)

4. **Dashboard Charts**:
   - Bar charts for regional comparison
   - Pie charts for overall electrification status
   - Line charts for confidence thresholds analysis
   - Scatter plots for uncertainty analysis (std_dev vs mean)

## Best Practices

1. **Caching**: Cache API responses to reduce server load, especially for static data like administrative boundaries.

2. **Progressive Loading**: Load data progressively based on zoom level
   - National/regional level at low zoom
   - Detailed building data at high zoom

3. **Performance Optimization**:
   - Use vector tiles instead of individual GeoJSON features
   - Apply filters on the server side when possible
   - Limit the number of buildings displayed at once
   - Use clustering for dense building areas

4. **Error Handling**:
   - Always include proper error handling for API requests
   - Provide meaningful feedback to users when data is unavailable

5. **Responsiveness**:
   - Ensure visualizations work well on mobile devices
   - Optimize layout for different screen sizes

## Examples

### Dashboard Integration Example

```javascript
// Fetch national metrics and update dashboard
async function updateDashboard() {
  try {
    const response = await fetch('http://localhost:8008/api/v1/metrics/national');
    const data = await response.json();
    
    document.getElementById('total-buildings').textContent = data.national_statistics.total_buildings.toLocaleString();
    document.getElementById('electrification-rate').textContent = data.national_statistics.electrification_rate.toFixed(1) + '%';
    document.getElementById('high-confidence-rate').textContent = data.national_statistics.high_confidence_rates['90_percent'].toFixed(1) + '%';
    document.getElementById('total-consumption').textContent = 
      Math.round(data.energy_planning.total_estimated_monthly_consumption).toLocaleString() + ' kWh/month';
    
    // Update charts
    updateElectrificationChart(data.national_statistics);
    updateRegionalComparisonChart(data.geographic_insights);
    updateConfidenceAnalysisChart(data.confidence_analysis);
  } catch (error) {
    console.error('Failed to fetch metrics:', error);
    document.getElementById('dashboard-error').textContent = 'Failed to load metrics. Please try again.';
  }
}

// Example chart using Chart.js
function updateElectrificationChart(statistics) {
  const ctx = document.getElementById('electrification-chart').getContext('2d');
  new Chart(ctx, {
    type: 'pie',
    data: {
      labels: ['Electrified', 'Unelectrified'],
      datasets: [{
        data: [statistics.electrified_buildings, statistics.unelectrified_buildings],
        backgroundColor: ['#4CAF50', '#F44336']
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: 'right',
        },
        title: {
          display: true,
          text: 'Electrification Status'
        }
      }
    }
  });
}
```

### Priority Zones Visualization

```javascript
async function visualizePriorityZones() {
  try {
    const response = await fetch('http://localhost:8008/api/v1/metrics/priority-zones');
    const data = await response.json();
    
    // Add electrification priority zones to the map
    const priorityFeatures = data.electrification_priority_zones.map(zone => ({
      type: 'Feature',
      properties: {
        name: zone.name,
        level: zone.level,
        electrification_rate: zone.electrification_rate,
        total_buildings: zone.total_buildings,
        priority_type: 'electrification'
      },
      geometry: null // You'll need to fetch the actual geometry from admin boundaries
    }));
    
    // Fetch boundaries for these zones
    const zoneNames = data.electrification_priority_zones.map(zone => zone.name);
    fetchAndDisplayZoneBoundaries(zoneNames, priorityFeatures);
  } catch (error) {
    console.error('Failed to fetch priority zones:', error);
  }
}

// Function to fetch and display zone boundaries
async function fetchAndDisplayZoneBoundaries(zoneNames, features) {
  // In a real implementation, you would fetch boundaries from your API
  // or query the vector tiles directly
  
  // Example: Add features to map
  map.addSource('priority-zones', {
    type: 'geojson',
    data: {
      type: 'FeatureCollection',
      features: features
    }
  });
  
  map.addLayer({
    id: 'priority-zones-layer',
    type: 'fill',
    source: 'priority-zones',
    paint: {
      'fill-color': '#F44336',
      'fill-opacity': 0.7,
      'fill-outline-color': '#000'
    }
  });
}
```

### Uncertainty Analysis Visualization

```javascript
async function visualizeUncertaintyAnalysis() {
  try {
    const response = await fetch('http://localhost:8008/api/v1/metrics/uncertainty-analysis');
    const data = await response.json();
    
    // Create scatter plot of communes by uncertainty
    const allCommunes = [
      ...data.high_uncertainty_communes.map(c => ({...c, category: 'high'})),
      ...data.medium_uncertainty_communes.map(c => ({...c, category: 'medium'})),
      ...data.low_uncertainty_communes.map(c => ({...c, category: 'low'}))
    ];
    
    const ctx = document.getElementById('uncertainty-chart').getContext('2d');
    new Chart(ctx, {
      type: 'scatter',
      data: {
        datasets: [
          {
            label: 'High Uncertainty',
            data: data.high_uncertainty_communes.map(c => ({
              x: c.avg_consumption_kwh_month,
              y: c.avg_std_consumption_kwh_month,
            })),
            backgroundColor: '#F44336'
          },
          {
            label: 'Medium Uncertainty',
            data: data.medium_uncertainty_communes.map(c => ({
              x: c.avg_consumption_kwh_month,
              y: c.avg_std_consumption_kwh_month,
            })),
            backgroundColor: '#FF9800'
          },
          {
            label: 'Low Uncertainty',
            data: data.low_uncertainty_communes.map(c => ({
              x: c.avg_consumption_kwh_month,
              y: c.avg_std_consumption_kwh_month,
            })),
            backgroundColor: '#FFEB3B'
          }
        ]
      },
      options: {
        scales: {
          x: {
            title: {
              display: true,
              text: 'Average Consumption (kWh/month)'
            }
          },
          y: {
            title: {
              display: true,
              text: 'Standard Deviation (kWh/month)'
            }
          }
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: function(context) {
                const index = context.dataIndex;
                const dataset = context.dataset;
                const communeIndex = allCommunes.findIndex(c => 
                  c.avg_consumption_kwh_month === context.parsed.x && 
                  c.avg_std_consumption_kwh_month === context.parsed.y
                );
                if (communeIndex >= 0) {
                  const commune = allCommunes[communeIndex];
                  return [
                    `Name: ${commune.name}`,
                    `Region: ${commune.region_name}`,
                    `Avg. Consumption: ${commune.avg_consumption_kwh_month.toFixed(2)} kWh/month`,
                    `Std. Deviation: ${commune.avg_std_consumption_kwh_month.toFixed(2)}`,
                    `Std/Avg Ratio: ${commune.std_dev_ratio.toFixed(2)}`
                  ];
                }
                return '';
              }
            }
          }
        }
      }
    });
  } catch (error) {
    console.error('Failed to fetch uncertainty analysis:', error);
  }
}
```

---

For more information, refer to the full [API documentation](http://localhost:8008/docs) which is available when the server is running. 