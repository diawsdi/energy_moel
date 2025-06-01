# Village Search API Documentation

This guide provides comprehensive documentation for the village search functionality, enabling frontend developers to implement location-based search and village selection features for electrification analysis projects.

## Overview

The Village Search API allows users to search for villages by name across Senegal, providing geographic coordinates and administrative context. This is essential for:

- **Location-based Project Creation**: Users can search and select specific villages for analysis
- **Geographic Navigation**: Quickly locate and zoom to specific villages on maps
- **Administrative Context**: Understanding which commune a village belongs to
- **Data Validation**: Verifying village names and locations before analysis

### Key Features

- **Fuzzy Search**: Accent-insensitive partial matching
- **Administrative Hierarchy**: Results include commune information
- **Geographic Coordinates**: Precise longitude/latitude for mapping
- **Relevance Ranking**: Results ordered by match quality and name length
- **Pagination Support**: Configurable result limits

## API Endpoint

### Search Villages

**Endpoint:** `GET /api/v1/villages/search`

**Description:** Search for villages by name with fuzzy matching and administrative context.

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search text for village name |
| `limit` | integer | No | 10 | Maximum number of results to return (1-100) |

#### Response Format

**Success Response:** `200 OK`

```json
[
    {
        "id": "8956d92d-4d21-4ba0-a3f5-63ddc9b57ace",
        "display_name": "NDIAGNE - (BADEGNE OUOLOF)",
        "name": "NDIAGNE",
        "commune_name": "BADEGNE OUOLOF",
        "longitude": -16.45129873621423,
        "latitude": 15.468407420773394
    }
]
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier for the village |
| `display_name` | string | Formatted name: "Village Name - (Commune Name)" |
| `name` | string | Original village name |
| `commune_name` | string | Name of the commune containing the village |
| `longitude` | float | Geographic longitude coordinate (WGS84) |
| `latitude` | float | Geographic latitude coordinate (WGS84) |

## Search Behavior

### Fuzzy Matching

The search implements intelligent fuzzy matching:

1. **Exact Match Priority**: Exact name matches appear first
2. **Partial Matching**: Supports substring searches
3. **Accent Insensitive**: Handles accented characters (é, è, ñ, etc.)
4. **Case Insensitive**: Works with any case combination

### Ranking Algorithm

Results are ranked by:
1. **Exact matches** (highest priority)
2. **Partial matches** (secondary priority)
3. **Name length** (shorter names first within same match type)

### Examples

#### Exact Search
```bash
GET /api/v1/villages/search?query=NDIAGNE&limit=3
```

Returns villages with exact name "NDIAGNE":
```json
[
    {
        "id": "f46bc7cf-0af7-4553-92bc-23e7cca2fc19",
        "display_name": "NDIAGNE - (LAMBAYE)",
        "name": "NDIAGNE",
        "commune_name": "LAMBAYE",
        "longitude": -16.5682608916503,
        "latitude": 14.79081306837513
    },
    {
        "id": "827e403c-23f1-49c1-b2ef-918db9576072",
        "display_name": "NDIAGNE - (THIENABA)",
        "name": "NDIAGNE",
        "commune_name": "THIENABA",
        "longitude": -16.790761789678164,
        "latitude": 14.823191792218312
    }
]
```

#### Partial Search
```bash
GET /api/v1/villages/search?query=ndiag&limit=5
```

Returns villages containing "ndiag":
```json
[
    {
        "id": "f4dbdc61-4a39-419a-8b88-ef1b4af7e9b2",
        "display_name": "NDIAGO - (NDIAGO)",
        "name": "NDIAGO",
        "commune_name": "NDIAGO",
        "longitude": -15.895647462089359,
        "latitude": 14.317207077782713
    },
    {
        "id": "f46bc7cf-0af7-4553-92bc-23e7cca2fc19",
        "display_name": "NDIAGNE - (LAMBAYE)",
        "name": "NDIAGNE",
        "commune_name": "LAMBAYE",
        "longitude": -16.5682608916503,
        "latitude": 14.79081306837513
    }
]
```

## Error Handling

### Missing Query Parameter

**Request:**
```bash
GET /api/v1/villages/search
```

**Response:** `422 Unprocessable Entity`
```json
{
    "detail": [
        {
            "type": "missing",
            "loc": ["query", "query"],
            "msg": "Field required",
            "input": null
        }
    ]
}
```

### No Results Found

**Request:**
```bash
GET /api/v1/villages/search?query=nonexistentvillage
```

**Response:** `200 OK`
```json
[]
```

### Invalid Limit Parameter

**Request:**
```bash
GET /api/v1/villages/search?query=test&limit=abc
```

**Response:** `422 Unprocessable Entity`
```json
{
    "detail": [
        {
            "type": "int_parsing",
            "loc": ["query", "limit"],
            "msg": "Input should be a valid integer",
            "input": "abc"
        }
    ]
}
```

## Integration Examples

### Basic JavaScript Implementation

```javascript
class VillageSearchService {
    constructor(baseUrl = 'http://localhost:8008/api/v1') {
        this.baseUrl = baseUrl;
    }
    
    async searchVillages(query, limit = 10) {
        if (!query || query.trim().length === 0) {
            throw new Error('Search query is required');
        }
        
        const params = new URLSearchParams({
            query: query.trim(),
            limit: Math.min(Math.max(1, limit), 100) // Clamp between 1-100
        });
        
        try {
            const response = await fetch(`${this.baseUrl}/villages/search?${params}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`Search failed: ${errorData.detail || response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Village search error:', error);
            throw error;
        }
    }
    
    async getVillagesByPrefix(prefix, maxResults = 5) {
        return this.searchVillages(prefix, maxResults);
    }
    
    async findExactVillage(name) {
        const results = await this.searchVillages(name, 50);
        return results.filter(village => 
            village.name.toLowerCase() === name.toLowerCase()
        );
    }
}

// Usage Examples
const villageService = new VillageSearchService();

// Basic search
const villages = await villageService.searchVillages('ndiagne');
console.log(`Found ${villages.length} villages`);

// Autocomplete functionality
const suggestions = await villageService.getVillagesByPrefix('ndia', 5);

// Find exact match
const exactMatches = await villageService.findExactVillage('NDIAGNE');
```

### React Hook Implementation

```javascript
import { useState, useEffect, useCallback } from 'react';

const useVillageSearch = (baseUrl = 'http://localhost:8008/api/v1') => {
    const [results, setResults] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    
    const searchVillages = useCallback(async (query, limit = 10) => {
        if (!query || query.trim().length === 0) {
            setResults([]);
            return;
        }
        
        setLoading(true);
        setError(null);
        
        try {
            const params = new URLSearchParams({
                query: query.trim(),
                limit: limit
            });
            
            const response = await fetch(`${baseUrl}/villages/search?${params}`);
            
            if (!response.ok) {
                throw new Error(`Search failed: ${response.status}`);
            }
            
            const villages = await response.json();
            setResults(villages);
        } catch (err) {
            setError(err.message);
            setResults([]);
        } finally {
            setLoading(false);
        }
    }, [baseUrl]);
    
    return {
        results,
        loading,
        error,
        searchVillages,
        clearResults: () => setResults([]),
        clearError: () => setError(null)
    };
};

// Usage in React Component
const VillageSearchComponent = () => {
    const [searchTerm, setSearchTerm] = useState('');
    const { results, loading, error, searchVillages } = useVillageSearch();
    
    useEffect(() => {
        const debounceTimer = setTimeout(() => {
            if (searchTerm.length >= 2) {
                searchVillages(searchTerm, 10);
            }
        }, 300);
        
        return () => clearTimeout(debounceTimer);
    }, [searchTerm, searchVillages]);
    
    return (
        <div className="village-search">
            <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search for a village..."
                className="search-input"
            />
            
            {loading && <div className="loading">Searching...</div>}
            {error && <div className="error">Error: {error}</div>}
            
            <div className="results">
                {results.map(village => (
                    <div key={village.id} className="village-item">
                        <h4>{village.display_name}</h4>
                        <p>Coordinates: {village.latitude}, {village.longitude}</p>
                    </div>
                ))}
            </div>
        </div>
    );
};
```

### Autocomplete/Typeahead Implementation

```javascript
class VillageAutocomplete {
    constructor(inputElement, onSelect, options = {}) {
        this.input = inputElement;
        this.onSelect = onSelect;
        this.options = {
            minLength: 2,
            maxResults: 8,
            debounceMs: 300,
            ...options
        };
        
        this.villageService = new VillageSearchService();
        this.setupEventListeners();
        this.createDropdown();
    }
    
    setupEventListeners() {
        let debounceTimer;
        
        this.input.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                this.handleInput(e.target.value);
            }, this.options.debounceMs);
        });
        
        this.input.addEventListener('blur', () => {
            setTimeout(() => this.hideDropdown(), 200);
        });
        
        this.input.addEventListener('focus', () => {
            if (this.input.value.length >= this.options.minLength) {
                this.handleInput(this.input.value);
            }
        });
    }
    
    createDropdown() {
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'village-dropdown';
        this.dropdown.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ccc;
            border-top: none;
            max-height: 200px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
        `;
        
        this.input.parentNode.style.position = 'relative';
        this.input.parentNode.appendChild(this.dropdown);
    }
    
    async handleInput(value) {
        if (value.length < this.options.minLength) {
            this.hideDropdown();
            return;
        }
        
        try {
            const villages = await this.villageService.searchVillages(
                value, 
                this.options.maxResults
            );
            this.showResults(villages);
        } catch (error) {
            console.error('Autocomplete search failed:', error);
            this.hideDropdown();
        }
    }
    
    showResults(villages) {
        if (villages.length === 0) {
            this.hideDropdown();
            return;
        }
        
        this.dropdown.innerHTML = villages.map(village => `
            <div class="village-option" data-village='${JSON.stringify(village)}'>
                <strong>${village.name}</strong>
                <br>
                <small>${village.commune_name}</small>
            </div>
        `).join('');
        
        // Add click handlers
        this.dropdown.querySelectorAll('.village-option').forEach(option => {
            option.addEventListener('click', () => {
                const village = JSON.parse(option.dataset.village);
                this.selectVillage(village);
            });
        });
        
        this.dropdown.style.display = 'block';
    }
    
    selectVillage(village) {
        this.input.value = village.display_name;
        this.hideDropdown();
        this.onSelect(village);
    }
    
    hideDropdown() {
        this.dropdown.style.display = 'none';
    }
}

// Usage
const searchInput = document.getElementById('villageSearch');
const autocomplete = new VillageAutocomplete(searchInput, (selectedVillage) => {
    console.log('Selected village:', selectedVillage);
    // Center map on village coordinates
    map.flyTo([selectedVillage.latitude, selectedVillage.longitude], 14);
});
```

### Map Integration Example

```javascript
// MapLibre/Leaflet integration
class VillageMapIntegration {
    constructor(map, villageService) {
        this.map = map;
        this.villageService = villageService;
        this.markers = [];
    }
    
    async searchAndShowVillages(query) {
        try {
            // Clear existing markers
            this.clearMarkers();
            
            // Search for villages
            const villages = await this.villageService.searchVillages(query, 20);
            
            if (villages.length === 0) {
                alert('No villages found for this search');
                return;
            }
            
            // Add markers for each village
            villages.forEach(village => {
                const marker = new maplibregl.Marker()
                    .setLngLat([village.longitude, village.latitude])
                    .setPopup(new maplibregl.Popup().setHTML(`
                        <h3>${village.name}</h3>
                        <p>Commune: ${village.commune_name}</p>
                        <p>Coordinates: ${village.latitude.toFixed(4)}, ${village.longitude.toFixed(4)}</p>
                        <button onclick="selectVillageForProject('${village.id}')">
                            Select for Project
                        </button>
                    `))
                    .addTo(this.map);
                
                this.markers.push(marker);
            });
            
            // Fit map to show all villages
            if (villages.length === 1) {
                this.map.flyTo({
                    center: [villages[0].longitude, villages[0].latitude],
                    zoom: 14
                });
            } else {
                const bounds = this.calculateBounds(villages);
                this.map.fitBounds(bounds, { padding: 50 });
            }
            
        } catch (error) {
            console.error('Error searching and displaying villages:', error);
            alert('Error searching for villages');
        }
    }
    
    calculateBounds(villages) {
        const lngs = villages.map(v => v.longitude);
        const lats = villages.map(v => v.latitude);
        
        return [
            [Math.min(...lngs), Math.min(...lats)], // Southwest
            [Math.max(...lngs), Math.max(...lats)]  // Northeast
        ];
    }
    
    clearMarkers() {
        this.markers.forEach(marker => marker.remove());
        this.markers = [];
    }
    
    focusOnVillage(villageId) {
        // Find and focus on specific village
        const marker = this.markers.find(m => m.villageId === villageId);
        if (marker) {
            this.map.flyTo({
                center: marker.getLngLat(),
                zoom: 16
            });
            marker.togglePopup();
        }
    }
}

// Usage with project creation
window.selectVillageForProject = async (villageId) => {
    try {
        // This would integrate with your project creation workflow
        const village = currentSearchResults.find(v => v.id === villageId);
        if (village) {
            // Create a bounding box around the village (e.g., 1km radius)
            const radius = 0.01; // Roughly 1km in degrees
            const polygon = {
                type: "Polygon",
                coordinates: [[
                    [village.longitude - radius, village.latitude - radius],
                    [village.longitude + radius, village.latitude - radius],
                    [village.longitude + radius, village.latitude + radius],
                    [village.longitude - radius, village.latitude + radius],
                    [village.longitude - radius, village.latitude - radius]
                ]]
            };
            
            // Add to current project
            await createProjectArea(currentProjectId, {
                geometry: polygon,
                name: `${village.name} Area`,
                area_type: "village"
            });
            
            alert(`Added ${village.name} to project`);
        }
    } catch (error) {
        console.error('Error adding village to project:', error);
        alert('Error adding village to project');
    }
};
```

## Use Cases and Workflows

### 1. Project Creation with Village Selection

```javascript
async function createProjectForVillage() {
    // Step 1: Search for village
    const villages = await villageService.searchVillages('ndiagne');
    
    // Step 2: Let user select specific village
    const selectedVillage = villages[0]; // User selection logic here
    
    // Step 3: Create project
    const project = await createProject({
        name: `Electrification Analysis - ${selectedVillage.name}`,
        description: `Analysis for ${selectedVillage.name} in ${selectedVillage.commune_name}`,
        organization_type: "government"
    });
    
    // Step 4: Create area around village
    const radius = 0.005; // Adjust based on needs
    const polygon = createPolygonAroundPoint(
        selectedVillage.longitude, 
        selectedVillage.latitude, 
        radius
    );
    
    const area = await createProjectArea(project.id, {
        geometry: polygon,
        name: `${selectedVillage.name} Analysis Area`,
        area_type: "village"
    });
    
    return { project, area, village: selectedVillage };
}
```

### 2. Multi-Village Project Creation

```javascript
async function createRegionalProject(villageNames) {
    const allVillages = [];
    
    // Search for all villages
    for (const name of villageNames) {
        const villages = await villageService.searchVillages(name);
        if (villages.length > 0) {
            allVillages.push(villages[0]); // Take first match
        }
    }
    
    // Create project
    const project = await createProject({
        name: `Regional Electrification Study`,
        description: `Multi-village analysis covering ${allVillages.length} villages`,
        organization_type: "government"
    });
    
    // Create areas for each village
    const areas = [];
    for (const village of allVillages) {
        const polygon = createPolygonAroundPoint(
            village.longitude, 
            village.latitude, 
            0.01
        );
        
        const area = await createProjectArea(project.id, {
            geometry: polygon,
            name: `${village.name} - ${village.commune_name}`,
            area_type: "village"
        });
        
        areas.push(area);
    }
    
    return { project, areas, villages: allVillages };
}
```

## Best Practices

### Performance Optimization

1. **Debounce Search Requests**: Wait 300ms after user stops typing
2. **Limit Results**: Use reasonable limits (5-20 results)
3. **Cache Results**: Cache recent searches locally
4. **Minimum Query Length**: Require at least 2-3 characters

### User Experience

1. **Loading States**: Show loading indicators during search
2. **Error Handling**: Provide clear error messages
3. **No Results Feedback**: Inform users when no villages are found
4. **Result Formatting**: Use the `display_name` for user-friendly display

### Data Integration

1. **Coordinate Validation**: Verify coordinates are within Senegal bounds
2. **Duplicate Handling**: Handle multiple villages with same name gracefully
3. **Administrative Context**: Use commune information for disambiguation
4. **Geographic Accuracy**: Validate coordinates before using for area creation

### Security Considerations

1. **Input Sanitization**: Sanitize search queries
2. **Rate Limiting**: Implement client-side rate limiting
3. **Error Information**: Don't expose sensitive error details
4. **API Endpoint Validation**: Validate API responses

## Testing

### Unit Tests

```javascript
describe('VillageSearchService', () => {
    let service;
    
    beforeEach(() => {
        service = new VillageSearchService();
    });
    
    test('should search villages successfully', async () => {
        const results = await service.searchVillages('ndiagne');
        expect(results).toBeInstanceOf(Array);
        expect(results.length).toBeGreaterThan(0);
        expect(results[0]).toHaveProperty('id');
        expect(results[0]).toHaveProperty('name');
        expect(results[0]).toHaveProperty('longitude');
        expect(results[0]).toHaveProperty('latitude');
    });
    
    test('should handle empty results', async () => {
        const results = await service.searchVillages('nonexistentvillage123');
        expect(results).toEqual([]);
    });
    
    test('should throw error for empty query', async () => {
        await expect(service.searchVillages('')).rejects.toThrow();
    });
});
```

### Integration Tests

```javascript
describe('Village Search Integration', () => {
    test('should integrate with map and project creation', async () => {
        // Search for village
        const villages = await villageService.searchVillages('ndiagne');
        expect(villages.length).toBeGreaterThan(0);
        
        // Create project with village
        const selectedVillage = villages[0];
        const project = await createProject({
            name: `Test Project - ${selectedVillage.name}`,
            organization_type: "government"
        });
        
        // Verify project creation
        expect(project.id).toBeDefined();
        expect(project.name).toContain(selectedVillage.name);
    });
});
```

This comprehensive documentation provides everything needed to implement robust village search functionality in your electrification analysis application.