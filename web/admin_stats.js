/**
 * Administrative Statistics Visualization Module
 * 
 * This module provides functionality to visualize statistics about buildings
 * across different administrative levels (region, department, arrondissement, commune).
 */

// Configuration
const CONFIG = {
    // Vector tile source URL
    vectorTileUrl: 'http://localhost:3015/admin_statistics_materialized',
    
    // Color schemes for different statistics
    colors: {
        electrificationRate: [
            'interpolate',
            ['linear'],
            ['get', 'electrification_rate'],
            0, '#d73027',    // 0% (dark red)
            25, '#fc8d59',   // 25% (orange)
            50, '#fee090',   // 50% (yellow)
            75, '#91cf60',   // 75% (light green)
            100, '#1a9850'   // 100% (dark green)
        ],
        highConfidenceRate50: [
            'interpolate',
            ['linear'],
            ['get', 'high_confidence_rate_50'],
            0, '#d73027',    // 0% (dark red)
            25, '#fc8d59',   // 25% (orange)
            50, '#fee090',   // 50% (yellow)
            75, '#91cf60',   // 75% (light green)
            100, '#1a9850'   // 100% (dark green)
        ],
        highConfidenceRate60: [
            'interpolate',
            ['linear'],
            ['get', 'high_confidence_rate_60'],
            0, '#d73027',    // 0% (dark red)
            25, '#fc8d59',   // 25% (orange)
            50, '#fee090',   // 50% (yellow)
            75, '#91cf60',   // 75% (light green)
            100, '#1a9850'   // 100% (dark green)
        ],
        highConfidenceRate70: [
            'interpolate',
            ['linear'],
            ['get', 'high_confidence_rate_70'],
            0, '#d73027',    // 0% (dark red)
            25, '#fc8d59',   // 25% (orange)
            50, '#fee090',   // 50% (yellow)
            75, '#91cf60',   // 75% (light green)
            100, '#1a9850'   // 100% (dark green)
        ],
        highConfidenceRate80: [
            'interpolate',
            ['linear'],
            ['get', 'high_confidence_rate_80'],
            0, '#d73027',    // 0% (dark red)
            25, '#fc8d59',   // 25% (orange)
            50, '#fee090',   // 50% (yellow)
            75, '#91cf60',   // 75% (light green)
            100, '#1a9850'   // 100% (dark green)
        ],
        highConfidenceRate85: [
            'interpolate',
            ['linear'],
            ['get', 'high_confidence_rate_85'],
            0, '#d73027',    // 0% (dark red)
            25, '#fc8d59',   // 25% (orange)
            50, '#fee090',   // 50% (yellow)
            75, '#91cf60',   // 75% (light green)
            100, '#1a9850'   // 100% (dark green)
        ],
        highConfidenceRate90: [
            'interpolate',
            ['linear'],
            ['get', 'high_confidence_rate_90'],
            0, '#d73027',    // 0% (dark red)
            25, '#fc8d59',   // 25% (orange)
            50, '#fee090',   // 50% (yellow)
            75, '#91cf60',   // 75% (light green)
            100, '#1a9850'   // 100% (dark green)
        ],
        buildingDensity: [
            'interpolate',
            ['linear'],
            ['get', 'total_buildings'],
            0, '#f7fcf5',      // Few buildings (very light green)
            100, '#c7e9c0',    // Some buildings (light green)
            500, '#74c476',    // More buildings (medium green)
            1000, '#31a354',   // Many buildings (dark green)
            5000, '#006d2c'    // Most buildings (very dark green)
        ],
        avgConsumption: [
            'interpolate',
            ['linear'],
            ['get', 'avg_consumption_kwh_month'],
            0, '#2166ac',     // Low consumption (blue)
            10, '#92c5de',    // Medium-low consumption (light blue)
            20, '#fddbc7',    // Medium-high consumption (light red)
            30, '#b2182b'     // High consumption (dark red)
        ],
        avgEnergyDemand: [
            'interpolate',
            ['linear'],
            ['get', 'avg_energy_demand_kwh_year'],
            0, '#2166ac',        // Low demand (blue)
            100, '#92c5de',      // Medium-low demand (light blue)
            500, '#fddbc7',      // Medium-high demand (light red)
            1000, '#b2182b'      // High demand (dark red)
        ],
        totalMonthlyConsumption: [
            'interpolate',
            ['linear'],
            ['*', ['get', 'total_buildings'], ['get', 'avg_consumption_kwh_month']],
            0, '#edf8fb',
            10000, '#b3cde3',
            50000, '#8c96c6',
            100000, '#8856a7',
            1000000, '#810f7c'
        ],
        totalYearlyDemand: [
            'interpolate',
            ['linear'],
            ['*', ['get', 'total_buildings'], ['get', 'avg_energy_demand_kwh_year']],
            0, '#edf8fb',
            50000, '#b3cde3',
            200000, '#8c96c6',
            1000000, '#8856a7',
            5000000, '#810f7c'
        ]
    },
    
    // Legend configurations for each statistic type
    legends: {
        electrificationRate: [
            { color: '#d73027', label: '0-25%' },
            { color: '#fc8d59', label: '25-50%' },
            { color: '#fee090', label: '50-75%' },
            { color: '#91cf60', label: '75-90%' },
            { color: '#1a9850', label: '90-100%' }
        ],
        highConfidenceRate50: [
            { color: '#d73027', label: '0-25%' },
            { color: '#fc8d59', label: '25-50%' },
            { color: '#fee090', label: '50-75%' },
            { color: '#91cf60', label: '75-90%' },
            { color: '#1a9850', label: '90-100%' }
        ],
        highConfidenceRate60: [
            { color: '#d73027', label: '0-25%' },
            { color: '#fc8d59', label: '25-50%' },
            { color: '#fee090', label: '50-75%' },
            { color: '#91cf60', label: '75-90%' },
            { color: '#1a9850', label: '90-100%' }
        ],
        highConfidenceRate70: [
            { color: '#d73027', label: '0-25%' },
            { color: '#fc8d59', label: '25-50%' },
            { color: '#fee090', label: '50-75%' },
            { color: '#91cf60', label: '75-90%' },
            { color: '#1a9850', label: '90-100%' }
        ],
        highConfidenceRate80: [
            { color: '#d73027', label: '0-25%' },
            { color: '#fc8d59', label: '25-50%' },
            { color: '#fee090', label: '50-75%' },
            { color: '#91cf60', label: '75-90%' },
            { color: '#1a9850', label: '90-100%' }
        ],
        highConfidenceRate85: [
            { color: '#d73027', label: '0-25%' },
            { color: '#fc8d59', label: '25-50%' },
            { color: '#fee090', label: '50-75%' },
            { color: '#91cf60', label: '75-90%' },
            { color: '#1a9850', label: '90-100%' }
        ],
        highConfidenceRate90: [
            { color: '#d73027', label: '0-25%' },
            { color: '#fc8d59', label: '25-50%' },
            { color: '#fee090', label: '50-75%' },
            { color: '#91cf60', label: '75-90%' },
            { color: '#1a9850', label: '90-100%' }
        ],
        buildingDensity: [
            { color: '#f7fcf5', label: '0-100 buildings' },
            { color: '#c7e9c0', label: '100-500 buildings' },
            { color: '#74c476', label: '500-1,000 buildings' },
            { color: '#31a354', label: '1,000-5,000 buildings' },
            { color: '#006d2c', label: '5,000+ buildings' }
        ],
        avgConsumption: [
            { color: '#2166ac', label: '0-10 kWh/month' },
            { color: '#92c5de', label: '10-20 kWh/month' },
            { color: '#fddbc7', label: '20-30 kWh/month' },
            { color: '#b2182b', label: '30+ kWh/month' }
        ],
        avgEnergyDemand: [
            { color: '#2166ac', label: '0-100 kWh/year' },
            { color: '#92c5de', label: '100-500 kWh/year' },
            { color: '#fddbc7', label: '500-1,000 kWh/year' },
            { color: '#b2182b', label: '1,000+ kWh/year' }
        ],
        totalMonthlyConsumption: [
            { color: '#edf8fb', label: '0-10,000 kWh/month' },
            { color: '#b3cde3', label: '10,000-50,000 kWh/month' },
            { color: '#8c96c6', label: '50,000-100,000 kWh/month' },
            { color: '#8856a7', label: '0.1-1 GWh/month' },
            { color: '#810f7c', label: '1+ GWh/month' }
        ],
        totalYearlyDemand: [
            { color: '#edf8fb', label: '0-50,000 kWh/year' },
            { color: '#b3cde3', label: '50,000-200,000 kWh/year' },
            { color: '#8c96c6', label: '0.2-1 GWh/year' },
            { color: '#8856a7', label: '1-5 GWh/year' },
            { color: '#810f7c', label: '5+ GWh/year' }
        ]
    }
};

// Current state
let currentState = {
    adminLevel: 'region',
    statType: 'electrificationRate',
    isVisible: false,
    labelsVisible: true,
    map: null
};

/**
 * Initialize the admin statistics module
 * @param {Object} mapInstance - MapLibre GL JS map instance
 */
function initAdminStats(mapInstance) {
    // Store map reference in currentState
    currentState.map = mapInstance;
    
    // Add the vector source
    currentState.map.addSource('admin-stats', {
        type: 'vector',
        url: CONFIG.vectorTileUrl
    });
    
    // Add the admin boundaries layer (initially hidden)
    currentState.map.addLayer({
        'id': 'admin-boundaries',
        'type': 'fill',
        'source': 'admin-stats',
        'source-layer': 'admin_statistics_materialized',
        'filter': ['==', ['get', 'level'], 'region'],
        'paint': {
            'fill-color': CONFIG.colors.electrificationRate,
            'fill-opacity': 0.7,
            'fill-outline-color': '#000000'
        },
        'layout': {
            'visibility': 'none'
        }
    });
    
    // Add outline layer for better visibility
    currentState.map.addLayer({
        'id': 'admin-boundaries-outline',
        'type': 'line',
        'source': 'admin-stats',
        'source-layer': 'admin_statistics_materialized',
        'filter': ['==', ['get', 'level'], 'region'],
        'paint': {
            'line-color': '#000000',
            'line-width': 1,
            'line-opacity': 0.7
        },
        'layout': {
            'visibility': 'none'
        }
    });
    
    // Add text labels for statistics
    currentState.map.addLayer({
        'id': 'admin-boundaries-labels',
        'type': 'symbol',
        'source': 'admin-stats',
        'source-layer': 'admin_statistics_materialized',
        'filter': ['==', ['get', 'level'], 'region'],
        'layout': {
            'visibility': 'none',
            'text-field': [
                'format',
                ['get', 'name'],
                { 'font-scale': 0.8 },
                '\n',
                {},
                [
                    'number-format',
                    ['get', 'electrification_rate'],
                    { 'min-fraction-digits': 1, 'max-fraction-digits': 1 }
                ],
                { 'font-scale': 1.2, 'font-weight': 'bold' },
                '%',
                {}
            ],
            'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold'],
            'text-size': [
                'interpolate',
                ['linear'],
                ['zoom'],
                5, 10,  // Smaller text at low zoom
                8, 14,  // Medium text at medium zoom
                12, 18  // Larger text at high zoom
            ],
            'text-anchor': 'center',
            'text-justify': 'center',
            'text-allow-overlap': false,
            'text-ignore-placement': false,
            'text-padding': 5,
            'symbol-sort-key': [   // Sort by admin level to prioritize display
                '*',
                ['case',
                    ['==', ['get', 'level'], 'region'], 1,
                    ['==', ['get', 'level'], 'department'], 2,
                    ['==', ['get', 'level'], 'arrondissement'], 3,
                    ['==', ['get', 'level'], 'commune'], 4,
                    5
                ],
                -1  // Negative to make smaller values (higher levels) appear first
            ]
        },
        'paint': {
            'text-color': '#000000',
            'text-halo-color': '#ffffff',
            'text-halo-width': 3
        },
        'maxzoom': 16
    });
    
    // Add click handler for popups
    currentState.map.on('click', 'admin-boundaries', function(e) {
        if (!e.features.length) return;
        
        const properties = e.features[0].properties;
        
        // Calculate total consumption and demand
        const totalBuildings = Number(properties.total_buildings);
        const avgConsumption = Number(properties.avg_consumption_kwh_month);
        const avgDemand = Number(properties.avg_energy_demand_kwh_year);
        
        const totalMonthlyConsumption = totalBuildings * avgConsumption;
        const totalYearlyDemand = totalBuildings * avgDemand;
        
        // Convert to GWh for display if values are large enough
        const totalMonthlyConsumptionDisplay = totalMonthlyConsumption >= 1000000 
            ? `${(totalMonthlyConsumption / 1000000).toFixed(2)} GWh/month` 
            : `${totalMonthlyConsumption.toLocaleString(undefined, {maximumFractionDigits: 0})} kWh/month`;
        
        const totalYearlyDemandDisplay = totalYearlyDemand >= 1000000 
            ? `${(totalYearlyDemand / 1000000).toFixed(2)} GWh/year` 
            : `${totalYearlyDemand.toLocaleString(undefined, {maximumFractionDigits: 0})} kWh/year`;
        
        // Format popup content
        const content = `
            <div class="popup-content">
                <h3>${properties.name} (${properties.level})</h3>
                <style>
                    .high-confidence {
                        background-color: #f0f9e8;
                        font-weight: bold;
                    }
                    .popup-content table {
                        width: 100%;
                        border-collapse: collapse;
                    }
                    .popup-content td {
                        padding: 4px;
                        border-bottom: 1px solid #eee;
                    }
                    .confidence-grid {
                        display: grid;
                        grid-template-columns: auto auto auto;
                        gap: 4px;
                        margin-top: 8px;
                        margin-bottom: 8px;
                        font-size: 0.9em;
                    }
                    .confidence-grid div {
                        padding: 3px;
                        text-align: center;
                        background: #333;
                    }
                    .confidence-header {
                        font-weight: bold;
                        background: #444 !important;
                    }
                    .total-energy {
                        background-color: #e5f5e0;
                        font-weight: bold;
                    }
                </style>
                <table>
                    <tr><td>Total Buildings:</td><td>${totalBuildings.toLocaleString()}</td></tr>
                    <tr><td>Electrified Buildings:</td><td>${Number(properties.electrified_buildings).toLocaleString()}</td></tr>
                    <tr><td>Unelectrified:</td><td>${Number(properties.unelectrified_buildings).toLocaleString()}</td></tr>
                    <tr><td colspan="2" class="high-confidence">High Confidence Electrification by Threshold:</td></tr>
                </table>
                <div class="confidence-grid">
                    <div class="confidence-header">Threshold</div>
                    <div class="confidence-header">Buildings</div>
                    <div class="confidence-header">Rate</div>
                    
                    <div>50%</div>
                    <div>${Number(properties.high_confidence_50).toLocaleString()}</div>
                    <div>${Number(properties.high_confidence_rate_50).toFixed(1)}%</div>
                    
                    <div>60%</div>
                    <div>${Number(properties.high_confidence_60).toLocaleString()}</div>
                    <div>${Number(properties.high_confidence_rate_60).toFixed(1)}%</div>
                    
                    <div>70%</div>
                    <div>${Number(properties.high_confidence_70).toLocaleString()}</div>
                    <div>${Number(properties.high_confidence_rate_70).toFixed(1)}%</div>
                    
                    <div>80%</div>
                    <div>${Number(properties.high_confidence_80).toLocaleString()}</div>
                    <div>${Number(properties.high_confidence_rate_80).toFixed(1)}%</div>
                    
                    <div>85%</div>
                    <div>${Number(properties.high_confidence_85).toLocaleString()}</div>
                    <div>${Number(properties.high_confidence_rate_85).toFixed(1)}%</div>
                    
                    <div>90%</div>
                    <div>${Number(properties.high_confidence_90).toLocaleString()}</div>
                    <div>${Number(properties.high_confidence_rate_90).toFixed(1)}%</div>
                </div>
                <table>
                    <tr><td>Avg. Consumption:</td><td>${avgConsumption.toFixed(2)} kWh/month</td></tr>
                    <tr><td>Avg. Energy Demand:</td><td>${avgDemand.toFixed(2)} kWh/year</td></tr>
                    <tr><td colspan="2" class="total-energy">Total Energy by Area:</td></tr>
                    <tr><td>Total Monthly Consumption:</td><td>${totalMonthlyConsumptionDisplay}</td></tr>
                    <tr><td>Total Yearly Demand:</td><td>${totalYearlyDemandDisplay}</td></tr>
                </table>
            </div>
        `;
        
        // Show popup
        new maplibregl.Popup()
            .setLngLat(e.lngLat)
            .setHTML(content)
            .addTo(currentState.map);
    });
    
    // Change cursor on hover
    currentState.map.on('mouseenter', 'admin-boundaries', function() {
        currentState.map.getCanvas().style.cursor = 'pointer';
    });
    
    currentState.map.on('mouseleave', 'admin-boundaries', function() {
        currentState.map.getCanvas().style.cursor = '';
    });
    
    // Create legend
    createLegend();
}

/**
 * Toggle the visibility of statistic labels
 * @param {Boolean} visible - Whether the labels should be visible
 */
function toggleLabels(visible) {
    currentState.labelsVisible = visible;
    
    // Only show labels if the main admin boundaries are also visible
    const finalVisibility = (currentState.isVisible && visible) ? 'visible' : 'none';
    currentState.map.setLayoutProperty('admin-boundaries-labels', 'visibility', finalVisibility);
}

/**
 * Toggle the visibility of admin statistics layers
 * @param {Boolean} visible - Whether the layers should be visible
 */
function toggleAdminStats(visible) {
    currentState.isVisible = visible;
    
    // Set visibility of boundary layers
    const visibility = visible ? 'visible' : 'none';
    currentState.map.setLayoutProperty('admin-boundaries', 'visibility', visibility);
    currentState.map.setLayoutProperty('admin-boundaries-outline', 'visibility', visibility);
    
    // Set visibility of label layer based on both overall visibility and label toggle
    const labelVisibility = (visible && currentState.labelsVisible) ? 'visible' : 'none';
    currentState.map.setLayoutProperty('admin-boundaries-labels', 'visibility', labelVisibility);
    
    // Show/hide legend
    const legend = document.getElementById('admin-legend');
    if (legend) {
        legend.style.display = visible ? 'block' : 'none';
    }
}

/**
 * Update the administrative level displayed
 * @param {String} level - The administrative level to display ('region', 'department', 'arrondissement', 'commune')
 */
function updateAdminLevel(level) {
    currentState.adminLevel = level;
    
    // Update layer filter to show only the selected level
    const filter = ['==', ['get', 'level'], level];
    currentState.map.setFilter('admin-boundaries', filter);
    currentState.map.setFilter('admin-boundaries-outline', filter);
    currentState.map.setFilter('admin-boundaries-labels', filter);
    
    // Update title in legend
    updateLegendTitle();
}

/**
 * Update the statistic type used for coloring
 * @param {String} statType - The type of statistic to visualize
 */
function updateStatType(statType) {
    currentState.statType = statType;
    
    // Update fill color based on selected statistic
    currentState.map.setPaintProperty('admin-boundaries', 'fill-color', CONFIG.colors[statType]);
    
    // Update labels to show the selected statistic
    updateLabels(statType);
    
    // Update legend
    updateLegend();
}

/**
 * Update the text labels to show the selected statistic
 * @param {String} statType - The type of statistic to visualize
 */
function updateLabels(statType) {
    let textField;
    
    switch(statType) {
        case 'electrificationRate':
            textField = [
                'format',
                ['get', 'name'],
                { 'font-scale': 0.8 },
                '\n',
                {},
                [
                    'number-format',
                    ['get', 'electrification_rate'],
                    { 'min-fraction-digits': 1, 'max-fraction-digits': 1 }
                ],
                { 'font-scale': 1.2, 'font-weight': 'bold' },
                '%',
                {}
            ];
            break;
        case 'highConfidenceRate50':
            textField = [
                'format',
                ['get', 'name'],
                { 'font-scale': 0.8 },
                '\n',
                {},
                [
                    'number-format',
                    ['get', 'high_confidence_rate_50'],
                    { 'min-fraction-digits': 1, 'max-fraction-digits': 1 }
                ],
                { 'font-scale': 1.2, 'font-weight': 'bold' },
                '%',
                {}
            ];
            break;
        case 'highConfidenceRate60':
            textField = [
                'format',
                ['get', 'name'],
                { 'font-scale': 0.8 },
                '\n',
                {},
                [
                    'number-format',
                    ['get', 'high_confidence_rate_60'],
                    { 'min-fraction-digits': 1, 'max-fraction-digits': 1 }
                ],
                { 'font-scale': 1.2, 'font-weight': 'bold' },
                '%',
                {}
            ];
            break;
        case 'highConfidenceRate70':
            textField = [
                'format',
                ['get', 'name'],
                { 'font-scale': 0.8 },
                '\n',
                {},
                [
                    'number-format',
                    ['get', 'high_confidence_rate_70'],
                    { 'min-fraction-digits': 1, 'max-fraction-digits': 1 }
                ],
                { 'font-scale': 1.2, 'font-weight': 'bold' },
                '%',
                {}
            ];
            break;
        case 'highConfidenceRate80':
            textField = [
                'format',
                ['get', 'name'],
                { 'font-scale': 0.8 },
                '\n',
                {},
                [
                    'number-format',
                    ['get', 'high_confidence_rate_80'],
                    { 'min-fraction-digits': 1, 'max-fraction-digits': 1 }
                ],
                { 'font-scale': 1.2, 'font-weight': 'bold' },
                '%',
                {}
            ];
            break;
        case 'highConfidenceRate85':
            textField = [
                'format',
                ['get', 'name'],
                { 'font-scale': 0.8 },
                '\n',
                {},
                [
                    'number-format',
                    ['get', 'high_confidence_rate_85'],
                    { 'min-fraction-digits': 1, 'max-fraction-digits': 1 }
                ],
                { 'font-scale': 1.2, 'font-weight': 'bold' },
                '%',
                {}
            ];
            break;
        case 'highConfidenceRate90':
            textField = [
                'format',
                ['get', 'name'],
                { 'font-scale': 0.8 },
                '\n',
                {},
                [
                    'number-format',
                    ['get', 'high_confidence_rate_90'],
                    { 'min-fraction-digits': 1, 'max-fraction-digits': 1 }
                ],
                { 'font-scale': 1.2, 'font-weight': 'bold' },
                '%',
                {}
            ];
            break;
        case 'buildingDensity':
            textField = [
                'format',
                ['get', 'name'],
                { 'font-scale': 0.8 },
                '\n',
                {},
                [
                    'number-format',
                    ['get', 'total_buildings'],
                    { 'min-fraction-digits': 0, 'max-fraction-digits': 0 }
                ],
                { 'font-scale': 1.2, 'font-weight': 'bold' }
            ];
            break;
        case 'avgConsumption':
            textField = [
                'format',
                ['get', 'name'],
                { 'font-scale': 0.8 },
                '\n',
                {},
                [
                    'number-format',
                    ['get', 'avg_consumption_kwh_month'],
                    { 'min-fraction-digits': 1, 'max-fraction-digits': 1 }
                ],
                { 'font-scale': 1.2, 'font-weight': 'bold' },
                ' kWh',
                {}
            ];
            break;
        case 'avgEnergyDemand':
            textField = [
                'format',
                ['get', 'name'],
                { 'font-scale': 0.8 },
                '\n',
                {},
                [
                    'number-format',
                    ['get', 'avg_energy_demand_kwh_year'],
                    { 'min-fraction-digits': 1, 'max-fraction-digits': 1 }
                ],
                { 'font-scale': 1.2, 'font-weight': 'bold' },
                ' kWh',
                {}
            ];
            break;
        case 'totalMonthlyConsumption':
            textField = [
                'format',
                ['get', 'name'],
                { 'font-scale': 0.8 },
                '\n',
                {},
                [
                    'case',
                    ['>=', ['*', ['get', 'total_buildings'], ['get', 'avg_consumption_kwh_month']], 1000000],
                    [
                        'concat',
                        [
                            'number-format',
                            ['/', ['*', ['get', 'total_buildings'], ['get', 'avg_consumption_kwh_month']], 1000000],
                            { 'min-fraction-digits': 2, 'max-fraction-digits': 2 }
                        ],
                        ' GWh'
                    ],
                    [
                        'concat',
                        [
                            'number-format',
                            ['*', ['get', 'total_buildings'], ['get', 'avg_consumption_kwh_month']],
                            { 'min-fraction-digits': 0, 'max-fraction-digits': 0 }
                        ],
                        ' kWh'
                    ]
                ],
                { 'font-scale': 1.2, 'font-weight': 'bold' }
            ];
            break;
        case 'totalYearlyDemand':
            textField = [
                'format',
                ['get', 'name'],
                { 'font-scale': 0.8 },
                '\n',
                {},
                [
                    'case',
                    ['>=', ['*', ['get', 'total_buildings'], ['get', 'avg_energy_demand_kwh_year']], 1000000],
                    [
                        'concat',
                        [
                            'number-format',
                            ['/', ['*', ['get', 'total_buildings'], ['get', 'avg_energy_demand_kwh_year']], 1000000],
                            { 'min-fraction-digits': 2, 'max-fraction-digits': 2 }
                        ],
                        ' GWh'
                    ],
                    [
                        'concat',
                        [
                            'number-format',
                            ['*', ['get', 'total_buildings'], ['get', 'avg_energy_demand_kwh_year']],
                            { 'min-fraction-digits': 0, 'max-fraction-digits': 0 }
                        ],
                        ' kWh'
                    ]
                ],
                { 'font-scale': 1.2, 'font-weight': 'bold' }
            ];
            break;
        default:
            textField = ['get', 'name'];
    }
    
    currentState.map.setLayoutProperty('admin-boundaries-labels', 'text-field', textField);
}

/**
 * Create the legend for admin statistics
 */
function createLegend() {
    // Create legend container if it doesn't exist
    if (!document.getElementById('admin-legend')) {
        const legend = document.createElement('div');
        legend.id = 'admin-legend';
        legend.className = 'map-overlay legend';
        legend.style.right = '10px';
        legend.style.bottom = '30px';
        legend.style.display = 'none'; // Initially hidden
        
        document.body.appendChild(legend);
    }
    
    // Initialize legend content
    updateLegend();
}

/**
 * Update the legend title based on current state
 */
function updateLegendTitle() {
    let title;
    switch(currentState.statType) {
        case 'electrificationRate':
            title = 'Electrification Rate';
            break;
        case 'highConfidenceRate50':
            title = 'High Confidence Electrification Rate (>50%)';
            break;
        case 'highConfidenceRate60':
            title = 'High Confidence Electrification Rate (>60%)';
            break;
        case 'highConfidenceRate70':
            title = 'High Confidence Electrification Rate (>70%)';
            break;
        case 'highConfidenceRate80':
            title = 'High Confidence Electrification Rate (>80%)';
            break;
        case 'highConfidenceRate85':
            title = 'High Confidence Electrification Rate (>85%)';
            break;
        case 'highConfidenceRate90':
            title = 'High Confidence Electrification Rate (>90%)';
            break;
        case 'buildingDensity':
            title = 'Building Density';
            break;
        case 'avgConsumption':
            title = 'Average Monthly Consumption';
            break;
        case 'avgEnergyDemand':
            title = 'Average Energy Demand';
            break;
        case 'totalMonthlyConsumption':
            title = 'Total Monthly Consumption';
            break;
        case 'totalYearlyDemand':
            title = 'Total Yearly Demand';
            break;
        default:
            title = 'Statistics';
    }
    
    return title + ' by ' + currentState.adminLevel.charAt(0).toUpperCase() + currentState.adminLevel.slice(1);
}

/**
 * Update the legend content
 */
function updateLegend() {
    const legend = document.getElementById('admin-legend');
    if (!legend) return;
    
    // Get current stat type legend items
    const legendItems = CONFIG.legends[currentState.statType];
    const title = updateLegendTitle();
    
    // Build HTML for legend
    let html = `<h4>${title}</h4>`;
    
    legendItems.forEach(item => {
        html += `<div><span style="background-color: ${item.color}"></span>${item.label}</div>`;
    });
    
    legend.innerHTML = html;
} 