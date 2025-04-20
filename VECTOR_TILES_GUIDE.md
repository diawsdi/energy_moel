# Vector Tiles Guide for Energy Infrastructure Visualization

This guide provides comprehensive documentation on how to use vector tiles with Martin and MapLibre GL JS for visualizing energy infrastructure data.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Martin Configuration](#martin-configuration)
4. [Data Preparation](#data-preparation)
5. [Web Visualization](#web-visualization)
6. [Performance Optimization](#performance-optimization)
7. [Troubleshooting](#troubleshooting)

## Overview

Vector tiles are a modern approach to web mapping that offers several advantages over traditional raster tiles:

- **Smaller file sizes**: Vector tiles are typically much smaller than raster tiles
- **Resolution independence**: Vector tiles look sharp at any zoom level
- **Dynamic styling**: Styling can be changed on the client-side without re-fetching tiles
- **Interactive features**: Vector tiles preserve feature attributes for interactive applications

In our energy infrastructure visualization, we use vector tiles to display:
- Building energy data (polygons)
- Power plants (points)
- Grid nodes/substations (points)
- Transmission lines (linestrings)

## Architecture

Our vector tile implementation consists of:

1. **PostgreSQL/PostGIS**: Stores spatial data in tables with geometry columns
2. **Martin**: A PostGIS vector tile server that generates vector tiles on-demand
3. **MapLibre GL JS**: A JavaScript library for rendering vector tiles in the browser

The data flow is as follows:
1. Spatial data is stored in PostgreSQL/PostGIS
2. Martin connects to PostgreSQL and serves vector tiles via a TileJSON endpoint
3. MapLibre GL JS requests tiles from Martin and renders them in the browser
4. User interactions are handled by MapLibre GL JS

## Martin Configuration

Martin is configured using a YAML file (`martin-config.yaml`). Here's how to configure it:

### Basic Configuration

```yaml
# Connection keep alive timeout
keep_alive: 120

# The socket address to bind
listen_addresses: '0.0.0.0:3000'

# Number of web server workers
worker_processes: 4

# Amount of memory (in MB) to use for caching tiles
cache_size_mb: 1024
```

### Database Connection

```yaml
postgres:
  # Database connection string with environment variable
  connection_string: '${DATABASE_URL:-postgresql://postgres:postgres@db:5432/energy_model}'

  # Maximum Postgres connections pool size
  pool_size: 20

  # Increase feature limit to handle large datasets
  max_feature_count: 500000
```

### Table Configuration

Each table that should be served as vector tiles needs to be configured:

```yaml
tables:
  buildings_energy:
    schema: public
    table: buildings_energy
    srid: 4326
    geometry_column: geom
    id_column: id
    minzoom: 0
    maxzoom: 22
    bounds: [-17.53, 12.33, -11.36, 16.69]  # Bounds for Senegal
    extent: 4096
    buffer: 128
    clip_geom: true
    geometry_type: GEOMETRY
    properties:
      id: int4
      area_in_meters: float8
      energy_demand_kwh: float8
      has_access: bool
      building_type: varchar
      year: int4
```

**Critical Parameters:**
- `geometry_column`: The column containing the geometry
- `properties`: All columns that should be included in the vector tiles
- `max_feature_count`: Increase this for large datasets
- `buffer`: Increase for smoother rendering at tile boundaries

## Data Preparation

### Requirements for Vector Tile-Ready Data

1. **Spatial Data**: Must be stored in PostGIS with a geometry column
2. **SRID**: Geometries should use EPSG:4326 (WGS 84) for compatibility
3. **Indexes**: Create spatial indexes for performance
4. **Simplified Geometries**: Consider simplifying complex geometries for better performance

### Example SQL for Creating a Vector Tile-Ready Table

```sql
CREATE TABLE buildings_energy (
    id BIGSERIAL PRIMARY KEY,
    geom GEOMETRY(Polygon, 4326),
    area_in_meters FLOAT,
    energy_demand_kwh FLOAT,
    has_access BOOLEAN,
    building_type VARCHAR(50),
    year INTEGER
);

-- Create spatial index
CREATE INDEX idx_buildings_energy_geom ON buildings_energy USING GIST (geom);
```

## Web Visualization

### Setting Up MapLibre GL JS

1. Include the MapLibre GL JS library:
```html
<link href="https://unpkg.com/maplibre-gl@3.3.1/dist/maplibre-gl.css" rel="stylesheet" />
<script src="https://unpkg.com/maplibre-gl@3.3.1/dist/maplibre-gl.js"></script>
```

2. Initialize the map:
```javascript
const map = new maplibregl.Map({
    container: 'map',
    style: {
        version: 8,
        sources: {
            // Base map source
            darkMap: {
                type: 'raster',
                tiles: ['https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png'],
                tileSize: 256
            }
        },
        layers: [
            {
                id: 'dark-map-tiles',
                type: 'raster',
                source: 'darkMap',
                minzoom: 0,
                maxzoom: 22
            }
        ]
    },
    center: [-14.5, 14.5],  // Center on Senegal
    zoom: 12
});
```

### Adding Vector Tile Sources

```javascript
map.on('load', function() {
    // Add the buildings source
    map.addSource('buildings', {
        type: 'vector',
        url: 'http://localhost:3000/buildings_energy',  // TileJSON endpoint
        minzoom: 0,
        maxzoom: 22
    });
    
    // Add other sources (power plants, grid nodes, grid lines)
    map.addSource('power_plants', {
        type: 'vector',
        url: 'http://localhost:3000/power_plants',
        minzoom: 0,
        maxzoom: 22
    });
});
```

### Adding Layers

```javascript
// Add a buildings layer with color based on energy demand
map.addLayer({
    'id': 'buildings-layer',
    'type': 'fill',
    'source': 'buildings',
    'source-layer': 'buildings_energy',
    'paint': {
        'fill-color': [
            'interpolate',
            ['linear'],
            ['case',
                ['has', 'energy_demand_kwh'], ['to-number', ['get', 'energy_demand_kwh']],
                0
            ],
            0, '#2166ac',        // 0 kWh (blue)
            100, '#4393c3',      // 100 kWh (medium blue)
            1000, '#92c5de',     // 1,000 kWh (light blue)
            10000, '#f7f7f7',    // 10,000 kWh (white)
            100000, '#fddbc7',   // 100,000 kWh (light red)
            1000000, '#d6604d',  // 1,000,000 kWh (medium red)
            10000000, '#b2182b'  // 10,000,000 kWh (dark red)
        ],
        'fill-opacity': 0.8,
        'fill-outline-color': '#000000'
    }
});
```

### Adding Interactivity

```javascript
// Add popup for buildings
map.on('click', 'buildings-layer', function(e) {
    if (!e.features.length) return;
    
    const feature = e.features[0];
    const properties = feature.properties;
    
    // Create popup content
    let content = '<div class="popup-content">';
    content += '<h3>Building Information</h3>';
    content += '<table>';
    
    if (properties.energy_demand_kwh !== undefined) {
        const demand = parseFloat(properties.energy_demand_kwh);
        content += `<tr><td>Energy Demand:</td><td>${Math.round(demand).toLocaleString()} kWh/year</td></tr>`;
    }
    
    content += '</table></div>';
    
    // Display popup
    new maplibregl.Popup()
        .setLngLat(e.lngLat)
        .setHTML(content)
        .addTo(map);
});

// Change cursor on hover
map.on('mouseenter', 'buildings-layer', function() {
    map.getCanvas().style.cursor = 'pointer';
});

map.on('mouseleave', 'buildings-layer', function() {
    map.getCanvas().style.cursor = '';
});
```

## Handling Low-Zoom Visibility

One common challenge with vector tiles is displaying small features (like buildings) at low zoom levels. There are two key approaches we've implemented to solve this:

### 1. Disabling Geometry Simplification in Martin

By default, Martin applies on-the-fly geometry simplification at low zoom levels, which can cause small features to disappear. To prevent this:

```yaml
tables:
  buildings_energy:
    # Other configuration...
    # Disable Douglas–Peucker simplification entirely
    simplify_tolerance: 0
```

This forces Martin to send the raw geometry at all zoom levels, preserving small features. Note that this comes at the cost of larger tile sizes.

### 2. Using Dual-Layer Representation

A more efficient approach is to use different visualization techniques at different zoom levels:

```javascript
// Polygon representation for high zoom levels
map.addLayer({
    'id': 'buildings-layer',
    'type': 'fill',
    'source': 'buildings',
    'source-layer': 'buildings_energy',
    'minzoom': 9,  // Only show building polygons at zoom level 9 and above
    'maxzoom': 22,
    'paint': {
        'fill-color': fillColor,
        'fill-opacity': 0.8,
        'fill-outline-color': '#000000'
    }
});

// Circle representation for low zoom levels
map.addLayer({
    'id': 'buildings-lowzoom-layer',
    'type': 'circle',
    'source': 'buildings',
    'source-layer': 'buildings_energy',
    'minzoom': 0,  // Show from the lowest zoom level
    'maxzoom': 9,  // Switch to polygons at zoom level 9
    'paint': {
        'circle-color': fillColor,
        'circle-radius': [
            'interpolate', ['linear'], ['zoom'],
            0, 1,     // 1px at zoom level 0
            5, 1.5,   // 1.5px at zoom level 5
            8, 2      // 2px at zoom level 8
        ],
        'circle-opacity': 0.8
    }
});
```

This approach:
- Uses circles (points) to represent buildings at low zoom levels (0-9)
- Switches to actual building polygons at higher zoom levels (9+)
- Maintains consistent styling and interactivity across both representations
- Significantly improves performance while ensuring features are always visible

### 3. Alternative: Clustering or Heatmaps

For very large datasets, consider using clustering or heatmaps at low zoom levels:

```javascript
map.addLayer({
    'id': 'buildings-heatmap',
    'type': 'heatmap',
    'source': 'buildings',
    'source-layer': 'buildings_energy',
    'minzoom': 0,
    'maxzoom': 9,
    'paint': {
        'heatmap-weight': [
            'interpolate', ['linear'], ['get', 'energy_demand_kwh'],
            0, 0,
            1000000, 1
        ],
        'heatmap-intensity': [
            'interpolate', ['linear'], ['zoom'],
            0, 1,
            9, 3
        ],
        'heatmap-color': [
            'interpolate', ['linear'], ['heatmap-density'],
            0, 'rgba(0, 0, 255, 0)',
            0.2, 'royalblue',
            0.4, 'cyan',
            0.6, 'lime',
            0.8, 'yellow',
            1, 'red'
        ],
        'heatmap-radius': [
            'interpolate', ['linear'], ['zoom'],
            0, 2,
            9, 20
        ],
        'heatmap-opacity': [
            'interpolate', ['linear'], ['zoom'],
            7, 1,
            9, 0
        ]
    }
});
```

## Performance Optimization

### Martin Configuration Optimization

1. **Increase cache size** for frequently accessed tiles:
```yaml
cache_size_mb: 2048  # Increase for better performance
```

2. **Adjust feature limits** based on your data:
```yaml
max_feature_count: 500000  # Increase for large datasets
```

3. **Optimize buffer size** for smoother rendering:
```yaml
buffer: 128  # Increase for complex geometries
```

### Database Optimization

1. **Create spatial indexes** on all geometry columns:
```sql
CREATE INDEX idx_buildings_geom ON buildings USING GIST (geom);
```

2. **Create attribute indexes** on frequently filtered columns:
```sql
CREATE INDEX idx_buildings_year ON buildings (year);
```

3. **Cluster tables** by spatial proximity:
```sql
CLUSTER buildings USING idx_buildings_geom;
```

### Client-Side Optimization

1. **Use appropriate zoom levels** for different layers:
```javascript
'minzoom': 10,  // Only show buildings at zoom level 10 and above
```

2. **Filter features** to reduce the number of rendered objects:
```javascript
'filter': ['>', ['to-number', ['get', 'energy_demand_kwh']], 1000]
```

3. **Simplify styling** for better performance:
```javascript
'line-simplification': 0.5  // Simplify lines for better performance
```

## Troubleshooting

### Common Issues and Solutions

1. **Missing Properties in Vector Tiles**
   - **Issue**: Properties not appearing in popups or not available for styling
   - **Solution**: Ensure properties are defined in the Martin configuration
   ```yaml
   properties:
     energy_demand_kwh: float8
     has_access: bool
   ```

2. **Slow Tile Generation**
   - **Issue**: Tiles take a long time to load
   - **Solution**: 
     - Increase Martin's pool_size
     - Add appropriate indexes in PostgreSQL
     - Consider simplifying geometries

3. **Data-Driven Styling Errors**
   - **Issue**: Errors like "data expressions not supported"
   - **Solution**: Some properties (like line-dasharray) don't support data-driven styling
     - Use multiple layers with filters instead
     - Use supported data-driven properties

4. **Type Conversion Issues**
   - **Issue**: Properties not displaying correctly or styling not working
   - **Solution**: Use explicit type conversion in MapLibre expressions
   ```javascript
   ['to-number', ['get', 'energy_demand_kwh']]
   ```

### Debugging Tips

1. **Check the browser console** for errors
2. **Inspect network requests** to see if tiles are being loaded
3. **Use map.showTileBoundaries = true** to visualize tile boundaries
4. **Check Martin logs** for server-side errors

## Conclusion

Vector tiles provide a powerful way to visualize large spatial datasets with interactive features. By properly configuring Martin and MapLibre GL JS, you can create high-performance, interactive visualizations of energy infrastructure data.

For more information, refer to:
- [Martin Documentation](https://github.com/maplibre/martin)
- [MapLibre GL JS Documentation](https://maplibre.org/maplibre-gl-js/docs/)
- [Vector Tile Specification](https://github.com/mapbox/vector-tile-spec)
