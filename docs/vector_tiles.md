# Vector Tile Integration Guide for Frontend Developers

This guide focuses on implementing vector tile layers for the key components of the energy grid visualization system: **buildings**, **unelectrified clusters**, **transmission lines**, and **grid nodes**.

## Quick Start: Essential Vector Layers

The Martin tile server at `http://localhost:3015` provides access to the following critical vector tile sources:

| Layer | Description | Endpoint | Source Layer |
|-------|-------------|----------|--------------|
| Buildings Energy | Buildings with energy consumption data | `http://localhost:3015/buildings_energy` | `buildings_energy` |
| Unelectrified Clusters | Areas without electricity access | `http://localhost:3015/unelectrified_clusters` | `unelectrified_clusters` |
| Transmission Lines | Power grid lines | `http://localhost:3015/grid_lines` | `grid_lines` |
| Grid Nodes | Substations and connection points | `http://localhost:3015/grid_nodes` | `grid_nodes` |
| Power Plants | Energy generation facilities | `http://localhost:3015/power_plants` | `power_plants` |

## CORS Configuration

To avoid CORS-related issues when fetching vector tiles from a different origin, ensure your Martin server is configured with appropriate CORS settings. Here's an example configuration in your `martin-config.yaml`:

```yaml
# CORS configuration
cors:
  # Allow all origins
  allowed_origins: ['*']
  # Allow all HTTP methods
  allowed_methods: ['GET', 'HEAD', 'OPTIONS']
  # Allow all HTTP headers
  allowed_headers: ['*']
  # Allow credentials
  allow_credentials: true
  # Set max age for preflight requests in seconds
  max_age_secs: 3600
```

## 1. Setting Up Buildings Layer

Buildings contain valuable information about energy consumption, electrification probability, and more.

```javascript
// Add the buildings source
map.addSource('buildings', {
    type: 'vector',
    url: 'http://localhost:3015/buildings_energy',
    minzoom: 0,
    maxzoom: 22
});

// Add the main buildings layer (polygons) for higher zoom levels
map.addLayer({
    'id': 'buildings-layer',
    'type': 'fill',
    'source': 'buildings',
    'source-layer': 'buildings_energy',
    'minzoom': 9,
    'maxzoom': 22,
    'paint': {
        'fill-color': [
            'interpolate',
            ['linear'],
            ['case',
                ['has', 'consumption_kwh_month'], ['to-number', ['get', 'consumption_kwh_month']],
                0
            ],
            0, '#2166ac',    // Very low consumption (dark blue)
            5, '#4393c3',    // Low consumption (medium blue)
            10, '#92c5de',   // Medium-low consumption (light blue)
            15, '#fddbc7',   // Medium-high consumption (light red)
            20, '#d6604d',   // High consumption (medium red)
            30, '#b2182b'    // Very high consumption (dark red)
        ],
        'fill-opacity': 0.8,
        'fill-outline-color': '#000000'
    }
});

// Add a low-zoom representation of buildings (circles) for lower zoom levels
map.addLayer({
    'id': 'buildings-lowzoom-layer',
    'type': 'circle',
    'source': 'buildings',
    'source-layer': 'buildings_energy',
    'minzoom': 0,
    'maxzoom': 9,
    'paint': {
        'circle-color': [
            'interpolate',
            ['linear'],
            ['case',
                ['has', 'consumption_kwh_month'], ['to-number', ['get', 'consumption_kwh_month']],
                0
            ],
            0, '#2166ac',    // Very low consumption (dark blue)
            5, '#4393c3',    // Low consumption (medium blue)
            10, '#92c5de',   // Medium-low consumption (light blue)
            15, '#fddbc7',   // Medium-high consumption (light red)
            20, '#d6604d',   // High consumption (medium red)
            30, '#b2182b'    // Very high consumption (dark red)
        ],
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

### Flexible Building Coloring Options

The visualization supports multiple coloring schemes for buildings:

```javascript
// Various fill-color options based on different properties

// 1. By monthly consumption (kWh/month)
'fill-color': [
    'interpolate',
    ['linear'],
    ['case',
        ['has', 'consumption_kwh_month'], ['to-number', ['get', 'consumption_kwh_month']],
        0
    ],
    0, '#2166ac',    // 0-5 kWh/month (dark blue)
    5, '#4393c3',    // 5-10 kWh/month (medium blue)
    10, '#92c5de',   // 10-15 kWh/month (light blue)
    15, '#fddbc7',   // 15-20 kWh/month (light red)
    20, '#d6604d',   // 20-30 kWh/month (medium red)
    30, '#b2182b'    // 30+ kWh/month (dark red)
]

// 2. By electrification probability (0-1)
'fill-color': [
    'interpolate',
    ['linear'],
    ['case',
        ['has', 'predicted_prob'], ['to-number', ['get', 'predicted_prob']],
        0
    ],
    0, '#d73027',    // 0-30% probability (dark red)
    0.3, '#fc8d59',  // 30-50% probability (orange red)
    0.5, '#fee090',  // 50-70% probability (light orange)
    0.7, '#e0f3f8',  // 70-90% probability (light blue)
    0.9, '#91bfdb',  // 90-100% probability (medium blue)
    1.0, '#4575b4'   // 100% probability (dark blue)
]

// 3. By annual energy demand (kWh/year)
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
]

// 4. By energy access status
'fill-color': [
    'case',
    ['==', ['get', 'has_access'], true], '#1a9850',  // Has access (green)
    ['==', ['get', 'has_access'], false], '#d73027', // No access (red)
    '#808080'  // Unknown (gray)
]

// 5. By building area (m²)
'fill-color': [
    'interpolate',
    ['linear'],
    ['case',
        ['has', 'area_in_meters'], ['to-number', ['get', 'area_in_meters']],
        0
    ],
    0, '#ffffcc',   // Very small buildings (light yellow)
    50, '#c2e699',  // Small buildings (light green)
    100, '#78c679', // Medium buildings (medium green)
    200, '#31a354', // Large buildings (dark green)
    500, '#006837'  // Very large buildings (very dark green)
]
```

### Building Properties

The building layer contains a rich set of properties useful for analysis and visualization:

- `id`: Unique identifier for the building
- `origin`: Data source identifier (e.g., "Google", "Microsoft", "OSM")
- `origin_id`: Original ID from the source dataset
- `area_in_meters`: Building footprint area in square meters
- `predicted_prob`: Probability of electrification (0-1 value)
- `predicted_electrified`: Binary classification (1 = electrified, 0 = not electrified)
- `consumption_kwh_month`: Estimated monthly energy consumption in kWh
- `std_consumption_kwh_month`: Standard deviation of consumption estimate
- `energy_demand_kwh`: Annual energy demand in kWh/year
- `has_access`: Boolean indicating if the building has electricity access
- `building_type`: Type classification of the building
- `year`: Year of the data

## 2. Setting Up Unelectrified Clusters

Unelectrified clusters represent geographical areas that need electricity. These clusters include valuable data about energy demand and distance to the nearest grid.

```javascript
// Add the unelectrified clusters source
map.addSource('unelectrified_clusters', {
    type: 'vector',
    url: 'http://localhost:3015/unelectrified_clusters',
    minzoom: 0,
    maxzoom: 22
});

// Add the fill layer for clusters
map.addLayer({
    'id': 'unelectrified-clusters-layer',
    'type': 'fill',
    'source': 'unelectrified_clusters',
    'source-layer': 'unelectrified_clusters',
    'paint': {
        // Color by energy demand
        'fill-color': [
            'case',
            ['>', ['get', 'total_energy_kwh'], 150], 'rgba(255, 0, 0, 0.2)',  // High demand (red)
            ['>', ['get', 'total_energy_kwh'], 75], 'rgba(255, 165, 0, 0.2)', // Medium demand (orange)
            'rgba(255, 255, 0, 0.2)'                                          // Low demand (yellow)
        ],
        'fill-opacity': 0.7
    }
});

// Add outline layer for better visibility
map.addLayer({
    'id': 'unelectrified-clusters-outline',
    'type': 'line',
    'source': 'unelectrified_clusters',
    'source-layer': 'unelectrified_clusters',
    'paint': {
        'line-color': [
            'case',
            ['>', ['get', 'total_energy_kwh'], 150], 'rgba(255, 0, 0, 0.9)',
            ['>', ['get', 'total_energy_kwh'], 75], 'rgba(255, 165, 0, 0.9)',
            'rgba(255, 255, 0, 0.9)'
        ],
        'line-width': 2
    }
});
```

### Key Cluster Properties

- `cluster_id`: Unique identifier for the cluster
- `total_buildings`: Number of buildings in the cluster
- `total_energy_kwh`: Total energy demand in kilowatt-hours
- `avg_energy_kwh`: Average energy demand per building
- `distance_to_grid_km`: Distance to the nearest grid line in kilometers

### Filtering Clusters by Distance to Grid

To show only clusters within a specific distance to the grid:

```javascript
// Show only clusters within 5km of the grid
map.addLayer({
    'id': 'near-grid-clusters',
    'type': 'fill',
    'source': 'unelectrified_clusters',
    'source-layer': 'unelectrified_clusters',
    'filter': ['<=', ['get', 'distance_to_grid_km'], 5],
    'paint': {
        'fill-color': 'rgba(0, 255, 0, 0.3)',
        'fill-outline-color': 'rgba(0, 255, 0, 0.8)'
    }
});
```

## 3. Displaying Transmission Lines

The grid lines show the power transmission network with different voltage levels.

```javascript
// Add the grid lines source
map.addSource('grid_lines', {
    type: 'vector',
    url: 'http://localhost:3015/grid_lines',
    minzoom: 0,
    maxzoom: 22
});

// Add the grid lines layer with styling by voltage
map.addLayer({
    'id': 'grid-lines-layer',
    'type': 'line',
    'source': 'grid_lines',
    'source-layer': 'grid_lines',
    'paint': {
        // Color by voltage level
        'line-color': [
            'match',
            ['get', 'voltage_kv'],
            30, '#ffd700',   // 30kV lines (gold)
            90, '#ff8c00',   // 90kV lines (dark orange)
            225, '#ff0000',  // 225kV lines (red)
            '#999999'        // Other voltages (gray)
        ],
        // Width that increases with zoom level
        'line-width': [
            'interpolate', ['linear'], ['zoom'],
            5, 1,   // Thin at low zoom
            10, 2,  // Medium at medium zoom
            15, 3   // Thick at high zoom
        ]
    },
    'layout': {
        'line-join': 'round',
        'line-cap': 'round'
    }
});
```

### Key Line Properties

- `line_id`: Unique identifier for the line
- `voltage_kv`: Voltage level in kilovolts
- `entity`: Entity or company that owns/operates the line
- `layer`: Additional categorization (often indicates if operational or planned)

## 4. Visualizing Grid Nodes

Grid nodes represent substations, transformers, and connection points in the transmission network.

```javascript
// Add the grid nodes source
map.addSource('grid_nodes', {
    type: 'vector',
    url: 'http://localhost:3015/grid_nodes',
    minzoom: 0,
    maxzoom: 22
});

// Add the grid nodes layer with styling by voltage
map.addLayer({
    'id': 'grid-nodes-layer',
    'type': 'circle',
    'source': 'grid_nodes',
    'source-layer': 'grid_nodes',
    'paint': {
        // Color by voltage level (matching the line colors)
        'circle-color': [
            'match',
            ['get', 'voltage_kv'],
            30, '#ffd700',
            90, '#ff8c00',
            225, '#ff0000',
            '#999999'
        ],
        // Size that increases with zoom level
        'circle-radius': [
            'interpolate', ['linear'], ['zoom'],
            5, 3,   // Small at low zoom
            10, 6,  // Medium at medium zoom
            15, 9   // Large at high zoom
        ],
        'circle-stroke-width': 2,
        'circle-stroke-color': '#ffffff'
    }
});
```

### Key Node Properties

- `node_id`: Unique identifier for the node
- `voltage_kv`: Voltage level in kilovolts
- `node_name`: Name of the substation or node
- `status`: Operational status (e.g., "OPR" for operational, "PLN" for planned)

## 5. Adding Power Plants Layer

Power plants represent energy generation facilities with various types and capacities.

```javascript
// Add the power plants source
map.addSource('power_plants', {
    type: 'vector',
    url: 'http://localhost:3015/power_plants',
    minzoom: 0,
    maxzoom: 22
});
    
// Add the power plants layer
map.addLayer({
    'id': 'power-plants-layer',
    'type': 'circle',
    'source': 'power_plants',
    'source-layer': 'power_plants',
    'paint': {
        // Color by plant type
        'circle-color': [
            'match',
            ['get', 'plant_type'],
            'THERMAL', '#ff7f00',  // Orange for thermal plants
            'HYDRO', '#1f78b4',    // Blue for hydro plants
            'SOLAR', '#ffff33',    // Yellow for solar plants
            'WIND', '#33a02c',     // Green for wind plants
            '#999999'              // Grey for other types
        ],
        'circle-radius': [
            'interpolate',
            ['linear'],
            ['zoom'],
            5, 5,    // Small at low zoom levels
            10, 10,  // Medium at medium zoom levels
            15, 15   // Large at high zoom levels
        ],
        'circle-stroke-width': 2,
        'circle-stroke-color': '#ffffff',
        'circle-opacity': 0.8
    }
});
```

### Power Plant Properties

- `plant_id`: Unique identifier for the power plant
- `plant_name`: Name of the power plant
- `plant_type`: Type of generation (THERMAL, HYDRO, SOLAR, WIND, etc.)
- `capacity_mw`: Generation capacity in megawatts
- `status`: Operational status (e.g., "OPR" for operational, "PLN" for planned)

## 6. Adding Interactive Popups

Building on our earlier examples, here's how to implement informative popups for buildings:

```javascript
// Add popup for buildings
map.on('click', 'buildings-layer', function(e) {
    if (!e.features.length) return;
    
    const properties = e.features[0].properties;
    
    // Format the popup content with energy information
    let content = '<div class="popup-content">';
    content += '<h3>Building Information</h3>';
    content += '<table>';
    
    if (properties.id) {
        content += `<tr><td>ID:</td><td>${properties.id}</td></tr>`;
    }
    
    if (properties.building_type) {
        content += `<tr><td>Type:</td><td>${properties.building_type}</td></tr>`;
    }
    
    if (properties.area_in_meters) {
        const area = parseFloat(properties.area_in_meters);
        content += `<tr><td>Area:</td><td>${Math.round(area)} m²</td></tr>`;
    }
    
    if (properties.energy_demand_kwh) {
        const demand = parseFloat(properties.energy_demand_kwh);
        content += `<tr><td>Annual Energy Demand:</td><td>${Math.round(demand).toLocaleString()} kWh/year</td></tr>`;
    }
    
    if (properties.consumption_kwh_month) {
        const consumption = parseFloat(properties.consumption_kwh_month);
        content += `<tr><td>Monthly Consumption:</td><td>${consumption.toFixed(2)} kWh/month</td></tr>`;
    }
    
    if (properties.std_consumption_kwh_month) {
        const std = parseFloat(properties.std_consumption_kwh_month);
        content += `<tr><td>Consumption Uncertainty:</td><td>±${std.toFixed(2)} kWh/month</td></tr>`;
    }
    
    if (properties.predicted_prob) {
        const prob = parseFloat(properties.predicted_prob);
        content += `<tr><td>Electrification Probability:</td><td>${(prob * 100).toFixed(1)}%</td></tr>`;
    }
    
    if (properties.has_access !== undefined) {
        const hasAccess = (properties.has_access === true || properties.has_access === 'true') ? true : false;
        content += `<tr><td>Has Access:</td><td>${hasAccess ? 'Yes' : 'No'}</td></tr>`;
    }
    
    if (properties.origin) {
        content += `<tr><td>Data Source:</td><td>${properties.origin}</td></tr>`;
    }
    
    content += '</table>';
    content += '</div>';
    
    // Display popup
    new maplibregl.Popup()
        .setLngLat(e.lngLat)
        .setHTML(content)
        .addTo(map);
});
```

## 7. Implementing Layer Toggle Controls

The application supports toggling visibility of various layers through checkbox controls:

```javascript
// Toggle buildings layer visibility
function toggleBuildings() {
    const isChecked = document.getElementById('showBuildings').checked;
    
    if (isChecked && !map.getLayer('buildings-layer')) {
        // Add the buildings layer if it doesn't exist yet
        addBuildingsLayer('energy_demand_kwh');
        document.getElementById('colorBy').disabled = false;
    } 
    else if (!isChecked && map.getLayer('buildings-layer')) {
        // Remove the buildings layer
        const buildingLayers = ['buildings-layer', 'buildings-lowzoom-layer'];
        buildingLayers.forEach(layerId => {
            if (map.getLayer(layerId)) {
                map.off('click', layerId);
                map.off('mouseenter', layerId);
                map.off('mouseleave', layerId);
                map.removeLayer(layerId);
            }
        });
        
        document.getElementById('legend').style.display = 'none';
        document.getElementById('colorBy').disabled = true;
    }
}

// Similar toggle functions for other layers
function togglePowerPlants() { /* ... */ }
function toggleGridNodes() { /* ... */ }
function toggleGridLines() { /* ... */ }
function toggleUnelectrifiedClusters() { /* ... */ }
```

## 8. Advanced: Dynamic Legend Updates

When changing the property used for coloring buildings, the legend should update accordingly:

```javascript
function updateLegend(property) {
    const legend = document.getElementById('legend');
    let title;

    // Hide specialized legends first
    document.getElementById('probability-legend').style.display = 'none';
    document.getElementById('consumption-legend').style.display = 'none';
    
    switch (property) {
        case 'energy_demand_kwh':
            title = 'Energy Demand (kWh)';
            break;
        case 'has_access':
            title = 'Energy Access';
            break;
        case 'area_in_meters':
            title = 'Building Area (m²)';
            break;
        case 'predicted_prob':
            title = 'Electrification Probability';
            document.getElementById('probability-legend').style.display = 'block';
            break;
        case 'consumption_kwh_month':
            title = 'Monthly Consumption (kWh)';
            document.getElementById('consumption-legend').style.display = 'block';
            break;
        default:
            title = 'Legend';
    }
    
    let html = `<h4>${title}</h4>`;
    
    // The content of each legend is defined in separate HTML elements
    legend.innerHTML = html;
}
```

## 9. Troubleshooting

### CORS Issues

If you encounter CORS errors like:

```
Access to fetch at 'http://localhost:3015/buildings_energy/9/232/234' from origin 'http://127.0.0.1:5500' has been blocked by CORS policy
```

Ensure your Martin configuration includes proper CORS headers as shown in the CORS Configuration section above. After updating the configuration, restart the Martin server:

```bash
docker-compose -f docker-compose.dev.yml restart martin
```

### Tile Loading Issues

If tiles fail to load or rendering is slow:

1. Check that the Martin server is running and accessible
2. Verify that your source URLs are correct
3. Increase the buffer size in your Martin configuration
4. Adjust the `max_feature_count` in Martin for layers with many features
5. Use appropriate zoom-dependent styling to improve performance

## 10. Complete Implementation Example

For a complete implementation example, refer to the `index.html` file which shows how all these components work together to create a comprehensive energy grid visualization.

The example demonstrates:
- Loading multiple vector tile sources
- Implementing different visualization styles for various properties
- Creating interactive popups with detailed information
- Building flexible controls for toggling layer visibility
- Dynamic legend updates based on selected properties 