# Project Creation API Documentation

This comprehensive guide provides frontend developers with everything needed to implement project creation and area management functionality for electrification insights analysis.

## Table of Contents

1. [Overview](#overview)
2. [Project Management Endpoints](#project-management-endpoints)
3. [Project Area Creation](#project-area-creation)
4. [File Upload Capabilities](#file-upload-capabilities)
5. [Geometry Validation & Analysis](#geometry-validation--analysis)
6. [Error Handling](#error-handling)
7. [Complete Integration Examples](#complete-integration-examples)
8. [Best Practices](#best-practices)

## Overview

The project creation system enables users to:
- Create and manage electrification analysis projects
- Define custom geographic areas for analysis
- Upload spatial data files (GeoJSON, Shapefiles)
- Validate and analyze geometry data
- Retrieve detailed energy statistics for defined areas

### Base URL
```
http://localhost:8008/api/v1
```

### Content Types
- JSON requests: `application/json`
- File uploads: `multipart/form-data`

## Project Management Endpoints

### 1. Create Project

Creates a new electrification analysis project.

**Endpoint:** `POST /projects/`

**Request Body:**
```json
{
    "name": "Rural Electrification Project 2024",
    "description": "Analysis of rural electrification opportunities in selected regions",
    "organization_type": "government"
}
```

**Required Fields:**
- `name` (string): Project name
- `organization_type` (string): Either "government" or "private"

**Optional Fields:**
- `description` (string): Project description

**Response:** `200 OK`
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Rural Electrification Project 2024",
    "description": "Analysis of rural electrification opportunities in selected regions",
    "organization_type": "government",
    "status": "draft",
    "created_by": "user123",
    "created_at": "2024-01-15T10:30:00.000Z",
    "updated_at": "2024-01-15T10:30:00.000Z",
    "areas": []
}
```

**JavaScript Example:**
```javascript
async function createProject(projectData) {
    try {
        const response = await fetch('http://localhost:8008/api/v1/projects/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(projectData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const project = await response.json();
        return project;
    } catch (error) {
        console.error('Error creating project:', error);
        throw error;
    }
}

// Usage
const newProject = await createProject({
    name: "Village Electrification Study",
    description: "Comprehensive analysis of electrification needs",
    organization_type: "government"
});
```

### 2. List Projects

Retrieves all projects with pagination support.

**Endpoint:** `GET /projects/`

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip (default: 0)
- `limit` (integer, optional): Maximum records to return (default: 100)

**Response:** `200 OK`
```json
[
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Rural Electrification Project 2024",
        "description": "Analysis of rural electrification opportunities",
        "organization_type": "government",
        "status": "draft",
        "created_by": "user123",
        "created_at": "2024-01-15T10:30:00.000Z",
        "updated_at": "2024-01-15T10:30:00.000Z",
        "areas": [
            {
                "id": "area-123",
                "name": "Village Area 1",
                "area_type": "village",
                "area_sq_km": 2.45,
                "created_at": "2024-01-15T11:00:00.000Z"
            }
        ]
    }
]
```

### 3. Get Single Project

Retrieves detailed information for a specific project.

**Endpoint:** `GET /projects/{project_id}`

**Response:** `200 OK`
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Rural Electrification Project 2024",
    "description": "Analysis of rural electrification opportunities",
    "organization_type": "government",
    "status": "draft",
    "created_by": "user123",
    "created_at": "2024-01-15T10:30:00.000Z",
    "updated_at": "2024-01-15T10:30:00.000Z",
    "areas": []
}
```

### 4. Update Project

Updates existing project information.

**Endpoint:** `PUT /projects/{project_id}`

**Request Body:**
```json
{
    "name": "Updated Project Name",
    "description": "Updated description",
    "status": "active"
}
```

**Response:** `200 OK`
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Updated Project Name",
    "description": "Updated description",
    "organization_type": "government",
    "status": "active",
    "created_by": "user123",
    "created_at": "2024-01-15T10:30:00.000Z",
    "updated_at": "2024-01-15T14:30:00.000Z",
    "areas": []
}
```

## Project Area Creation

### Enhanced Area Creation

Creates project areas with advanced geometry processing capabilities.

**Endpoint:** `POST /projects/{project_id}/areas/enhanced`

#### Scenario 1: Single Polygon from UI Drawing

**Request Body:**
```json
{
    "geometry": {
        "type": "Polygon",
        "coordinates": [
            [
                [-17.0, 14.5],
                [-16.8, 14.5],
                [-16.8, 14.7],
                [-17.0, 14.7],
                [-17.0, 14.5]
            ]
        ]
    },
    "name": "Village Analysis Area",
    "area_type": "village"
}
```

**Response:** `200 OK`
```json
{
    "id": "area-456",
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Village Analysis Area",
    "area_type": "village",
    "geometry": {
        "type": "MultiPolygon",
        "coordinates": [[
            [
                [-17.0, 14.5],
                [-16.8, 14.5],
                [-16.8, 14.7],
                [-17.0, 14.7],
                [-17.0, 14.5]
            ]
        ]]
    },
    "area_metadata": {
        "source": "drawn",
        "processing_method": "enhanced"
    },
    "source_type": "drawn",
    "processing_status": "completed",
    "area_sq_km": 484.32,
    "created_at": "2024-01-15T11:00:00.000Z",
    "updated_at": "2024-01-15T11:00:00.000Z"
}
```

#### Scenario 2: Multiple Polygons

**Request Body:**
```json
{
    "geometry": [
        {
            "type": "Polygon",
            "coordinates": [
                [
                    [-17.2, 14.1],
                    [-17.0, 14.1],
                    [-17.0, 14.3],
                    [-17.2, 14.3],
                    [-17.2, 14.1]
                ]
            ]
        },
        {
            "type": "Polygon",
            "coordinates": [
                [
                    [-16.8, 14.1],
                    [-16.6, 14.1],
                    [-16.6, 14.3],
                    [-16.8, 14.3],
                    [-16.8, 14.1]
                ]
            ]
        }
    ],
    "name": "Multiple Areas",
    "area_type": "custom"
}
```

**Response:** `200 OK` (Array of created areas)
```json
[
    {
        "id": "area-789",
        "project_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Multiple Areas (1)",
        "area_type": "custom",
        "area_sq_km": 484.32,
        "created_at": "2024-01-15T11:00:00.000Z"
    },
    {
        "id": "area-790",
        "project_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Multiple Areas (2)",
        "area_type": "custom",
        "area_sq_km": 484.32,
        "created_at": "2024-01-15T11:00:00.000Z"
    }
]
```

#### Scenario 3: GeoJSON Feature with Properties

**Request Body:**
```json
{
    "geometry": {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-15.8, 14.2],
                    [-15.6, 14.2],
                    [-15.6, 14.4],
                    [-15.8, 14.4],
                    [-15.8, 14.2]
                ]
            ]
        },
        "properties": {
            "village_name": "Test Village",
            "population": 950,
            "electrified": false
        }
    },
    "name": "Village with Properties",
    "area_type": "village"
}
```

**Response:** `200 OK`
```json
{
    "id": "area-101",
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Village with Properties",
    "area_type": "village",
    "geometry": {
        "type": "MultiPolygon",
        "coordinates": [[
            [
                [-15.8, 14.2],
                [-15.6, 14.2],
                [-15.6, 14.4],
                [-15.8, 14.4],
                [-15.8, 14.2]
            ]
        ]]
    },
    "area_metadata": {
        "source": "drawn",
        "properties": {
            "village_name": "Test Village",
            "population": 950,
            "electrified": false
        }
    },
    "area_sq_km": 484.32,
    "created_at": "2024-01-15T11:00:00.000Z"
}
```

#### Scenario 4: Overlapping Geometries with Merge

**Request Body:**
```json
{
    "geometry": [
        {
            "type": "Polygon",
            "coordinates": [
                [
                    [-14.8, 14.5],
                    [-14.6, 14.5],
                    [-14.6, 14.7],
                    [-14.8, 14.7],
                    [-14.8, 14.5]
                ]
            ]
        },
        {
            "type": "Polygon",
            "coordinates": [
                [
                    [-14.7, 14.6],
                    [-14.5, 14.6],
                    [-14.5, 14.8],
                    [-14.7, 14.8],
                    [-14.7, 14.6]
                ]
            ]
        }
    ],
    "name": "Overlapping Areas",
    "area_type": "custom",
    "merge_overlapping": true
}
```

**Response:** `200 OK`
```json
{
    "id": "area-102",
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Overlapping Areas (Merged)",
    "area_type": "custom",
    "area_metadata": {
        "source": "drawn",
        "merge_applied": true,
        "original_feature_count": 2
    },
    "area_sq_km": 726.48,
    "created_at": "2024-01-15T11:00:00.000Z"
}
```

**JavaScript Implementation:**
```javascript
async function createProjectArea(projectId, areaData) {
    try {
        const response = await fetch(`http://localhost:8008/api/v1/projects/${projectId}/areas/enhanced`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(areaData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error creating project area:', error);
        throw error;
    }
}
```

## File Upload Capabilities

### Enhanced File Upload

Supports uploading GeoJSON and Shapefile formats with advanced processing.

**Endpoint:** `POST /projects/{project_id}/areas/upload-enhanced`

#### GeoJSON File Upload

**Request:** `multipart/form-data`
```javascript
const formData = new FormData();
formData.append('file', geoJsonFile, 'areas.geojson');
formData.append('name', 'Uploaded Areas');
formData.append('area_type', 'village');

const response = await fetch(`http://localhost:8008/api/v1/projects/${projectId}/areas/upload-enhanced`, {
    method: 'POST',
    body: formData
});
```

**Response for Single Feature:** `200 OK`
```json
{
    "id": "area-103",
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Uploaded Areas",
    "area_type": "village",
    "geometry": {
        "type": "MultiPolygon",
        "coordinates": [...]
    },
    "area_metadata": {
        "source": "geojson_upload",
        "filename": "areas.geojson",
        "feature_index": 0
    },
    "source_type": "geojson_upload",
    "original_filename": "areas.geojson",
    "processing_status": "completed",
    "area_sq_km": 156.78,
    "created_at": "2024-01-15T12:00:00.000Z"
}
```

**Response for Multiple Features:** `200 OK`
```json
[
    {
        "id": "area-104",
        "name": "Uploaded Areas (1)",
        "area_sq_km": 156.78,
        "created_at": "2024-01-15T12:00:00.000Z"
    },
    {
        "id": "area-105",
        "name": "Uploaded Areas (2)",
        "area_sq_km": 243.56,
        "created_at": "2024-01-15T12:00:00.000Z"
    }
]
```

#### Shapefile Upload

**Request:** `multipart/form-data`
```javascript
const formData = new FormData();
formData.append('file', shapefileZip, 'areas.zip');
formData.append('name', 'Shapefile Areas');
formData.append('area_type', 'custom');

const response = await fetch(`http://localhost:8008/api/v1/projects/${projectId}/areas/upload-enhanced`, {
    method: 'POST',
    body: formData
});
```

**Response:** `200 OK`
```json
[
    {
        "id": "area-106",
        "project_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Shapefile Areas (1)",
        "area_type": "custom",
        "area_metadata": {
            "source": "shapefile",
            "filename": "areas.zip",
            "feature_index": 0,
            "attributes": {
                "NAME": "Village A",
                "POPULATION": "1250",
                "ELECTRIFIED": "false"
            }
        },
        "source_type": "shapefile",
        "original_filename": "areas.zip",
        "processing_status": "completed",
        "area_sq_km": 89.34,
        "created_at": "2024-01-15T12:15:00.000Z"
    }
]
```

### Batch File Upload

Upload multiple files simultaneously for processing.

**Endpoint:** `POST /projects/{project_id}/areas/batch-upload`

**Request:** `multipart/form-data`
```javascript
const formData = new FormData();
formData.append('files', file1, 'area1.geojson');
formData.append('files', file2, 'area2.zip');
formData.append('base_name', 'Batch Upload');
formData.append('area_type', 'village');

const response = await fetch(`http://localhost:8008/api/v1/projects/${projectId}/areas/batch-upload`, {
    method: 'POST',
    body: formData
});
```

**Response:** `200 OK`
```json
{
    "total_files_processed": 2,
    "successful_uploads": 2,
    "failed_uploads": 0,
    "created_areas": [
        {
            "id": "area-107",
            "name": "Batch Upload - area1",
            "source_file": "area1.geojson"
        },
        {
            "id": "area-108",
            "name": "Batch Upload - area2",
            "source_file": "area2.zip"
        }
    ],
    "errors": []
}
```

## Geometry Validation & Analysis

### Validate Geometry

Validates geometry data without creating areas.

**Endpoint:** `POST /projects/validate-geometry`

**Request Body:**
```json
{
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[-15.0, 14.0], [-14.8, 14.0], [-14.8, 14.2], [-15.0, 14.2], [-15.0, 14.0]]]
            }
        }
    ]
}
```

**Response:** `200 OK`
```json
{
    "is_valid": true,
    "geometry_info": {
        "total_features": 1,
        "geometry_types": ["Polygon"],
        "will_create_areas": 1,
        "has_overlapping_geometries": false,
        "bbox": [-15.0, 14.0, -14.8, 14.2]
    },
    "validation_details": {
        "valid_geometries": 1,
        "invalid_geometries": 0,
        "corrected_geometries": 0
    }
}
```

### Analyze Geometry

Provides detailed analysis of geometry data including area calculations.

**Endpoint:** `POST /projects/analyze-geometry`

**Request Body:**
```json
{
    "geometry_input": {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-15.0, 14.0], [-14.8, 14.0], [-14.8, 14.2], [-15.0, 14.2], [-15.0, 14.0]]]
                },
                "properties": {
                    "name": "Test Village"
                }
            }
        ]
    },
    "base_name": "Analysis Test"
}
```

**Response:** `200 OK`
```json
{
    "total_features": 1,
    "geometry_types": {
        "Polygon": 1
    },
    "will_create_areas": 1,
    "total_estimated_area_sq_km": 484.32,
    "feature_analysis": [
        {
            "feature_index": 0,
            "geometry_type": "Polygon",
            "area_sq_km": 484.32,
            "is_valid": true,
            "has_properties": true,
            "property_count": 1
        }
    ],
    "bbox": [-15.0, 14.0, -14.8, 14.2],
    "recommendations": {
        "merge_overlapping": false,
        "simplification_needed": false,
        "validation_required": false
    }
}
```

## Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
    "detail": "Invalid geometry format: coordinates must be a valid polygon"
}
```

#### 404 Not Found
```json
{
    "detail": "Project not found"
}
```

#### 422 Validation Error
```json
{
    "detail": [
        {
            "loc": ["body", "name"],
            "msg": "field required",
            "type": "value_error.missing"
        }
    ]
}
```

#### 500 Internal Server Error
```json
{
    "detail": "Error processing geometry: invalid coordinate reference system"
}
```

### Error Handling Best Practices

```javascript
async function handleApiCall(apiFunction) {
    try {
        const result = await apiFunction();
        return result;
    } catch (error) {
        if (error.response) {
            // HTTP error response
            const status = error.response.status;
            const data = await error.response.json();
            
            switch (status) {
                case 400:
                    throw new Error(`Invalid request: ${data.detail}`);
                case 404:
                    throw new Error(`Resource not found: ${data.detail}`);
                case 422:
                    const validationErrors = data.detail.map(err => err.msg).join(', ');
                    throw new Error(`Validation errors: ${validationErrors}`);
                case 500:
                    throw new Error(`Server error: ${data.detail}`);
                default:
                    throw new Error(`Unexpected error: ${data.detail || 'Unknown error'}`);
            }
        } else {
            // Network or other error
            throw new Error(`Network error: ${error.message}`);
        }
    }
}
```

## Complete Integration Examples

### Project Creation Workflow

```javascript
class ProjectManager {
    constructor(baseUrl = 'http://localhost:8008/api/v1') {
        this.baseUrl = baseUrl;
    }
    
    async createProject(projectData) {
        const response = await fetch(`${this.baseUrl}/projects/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(projectData)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to create project: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async addDrawnArea(projectId, geometry, name, areaType = 'village') {
        const areaData = {
            geometry: geometry,
            name: name,
            area_type: areaType
        };
        
        const response = await fetch(`${this.baseUrl}/projects/${projectId}/areas/enhanced`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(areaData)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to create area: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async uploadFile(projectId, file, name, areaType = 'village') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('name', name);
        formData.append('area_type', areaType);
        
        const response = await fetch(`${this.baseUrl}/projects/${projectId}/areas/upload-enhanced`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Failed to upload file: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async validateGeometry(geometry) {
        const response = await fetch(`${this.baseUrl}/projects/validate-geometry`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(geometry)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to validate geometry: ${response.status}`);
        }
        
        return await response.json();
    }
}

// Usage Example
const projectManager = new ProjectManager();

async function createProjectWithAreas() {
    try {
        // 1. Create project
        const project = await projectManager.createProject({
            name: "Rural Electrification Analysis",
            description: "Analysis of rural areas for electrification planning",
            organization_type: "government"
        });
        
        console.log(`Created project: ${project.id}`);
        
        // 2. Add a drawn area
        const drawnGeometry = {
            type: "Polygon",
            coordinates: [
                [
                    [-17.0, 14.5],
                    [-16.8, 14.5],
                    [-16.8, 14.7],
                    [-17.0, 14.7],
                    [-17.0, 14.5]
                ]
            ]
        };
        
        const area = await projectManager.addDrawnArea(
            project.id,
            drawnGeometry,
            "Target Village Area",
            "village"
        );
        
        console.log(`Created area: ${area.id} with ${area.area_sq_km} km²`);
        
        // 3. Upload a file (if user provides one)
        const fileInput = document.getElementById('fileInput');
        if (fileInput.files.length > 0) {
            const uploadedAreas = await projectManager.uploadFile(
                project.id,
                fileInput.files[0],
                "Uploaded Area",
                "custom"
            );
            
            console.log(`Uploaded ${Array.isArray(uploadedAreas) ? uploadedAreas.length : 1} areas`);
        }
        
        return project;
        
    } catch (error) {
        console.error('Error in project creation workflow:', error);
        throw error;
    }
}
```

### Form Integration Example

```html
<!-- Project Creation Form -->
<form id="projectForm">
    <div>
        <label for="projectName">Project Name:</label>
        <input type="text" id="projectName" required>
    </div>
    
    <div>
        <label for="projectDescription">Description:</label>
        <textarea id="projectDescription"></textarea>
    </div>
    
    <div>
        <label for="orgType">Organization Type:</label>
        <select id="orgType" required>
            <option value="government">Government</option>
            <option value="private">Private</option>
        </select>
    </div>
    
    <button type="submit">Create Project</button>
</form>

<!-- Area Definition Methods -->
<div id="areaDefinition" style="display: none;">
    <h3>Define Analysis Areas</h3>
    
    <!-- Method 1: Draw on Map -->
    <div>
        <h4>Method 1: Draw on Map</h4>
        <p>Use the drawing tools on the map to define areas</p>
        <button id="enableDrawing">Enable Drawing</button>
    </div>
    
    <!-- Method 2: Upload File -->
    <div>
        <h4>Method 2: Upload File</h4>
        <input type="file" id="fileUpload" accept=".geojson,.json,.zip">
        <input type="text" id="uploadName" placeholder="Area name">
        <select id="uploadAreaType">
            <option value="village">Village</option>
            <option value="custom">Custom</option>
        </select>
        <button id="uploadFile">Upload</button>
    </div>
    
    <!-- Method 3: Validate Before Adding -->
    <div>
        <h4>Method 3: Validate Geometry</h4>
        <textarea id="geometryInput" placeholder="Paste GeoJSON here"></textarea>
        <button id="validateGeometry">Validate</button>
        <div id="validationResult"></div>
    </div>
</div>

<script>
document.getElementById('projectForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const projectData = {
        name: document.getElementById('projectName').value,
        description: document.getElementById('projectDescription').value,
        organization_type: document.getElementById('orgType').value
    };
    
    try {
        const project = await projectManager.createProject(projectData);
        document.getElementById('areaDefinition').style.display = 'block';
        
        // Store project ID for area creation
        window.currentProjectId = project.id;
        
    } catch (error) {
        alert(`Error creating project: ${error.message}`);
    }
});

document.getElementById('uploadFile').addEventListener('click', async () => {
    const fileInput = document.getElementById('fileUpload');
    const name = document.getElementById('uploadName').value;
    const areaType = document.getElementById('uploadAreaType').value;
    
    if (!fileInput.files.length || !name) {
        alert('Please select a file and enter a name');
        return;
    }
    
    try {
        const result = await projectManager.uploadFile(
            window.currentProjectId,
            fileInput.files[0],
            name,
            areaType
        );
        
        console.log('Upload successful:', result);
        alert('File uploaded successfully!');
        
    } catch (error) {
        alert(`Upload failed: ${error.message}`);
    }
});

document.