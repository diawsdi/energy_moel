# Energy Model Backend

A FastAPI backend for managing and serving energy model data with PostgreSQL/PostGIS spatial database.

## Features

- RESTful API with FastAPI
- PostgreSQL with PostGIS for spatial data storage
- Efficient spatial queries for MapLibre and Martin vector tile rendering
- Batch data loading from GeoPackage files
- Docker Compose setup for easy deployment
- Administrative boundaries visualization with statistics
- Comprehensive metrics API for electrification analysis
- Uncertainty analysis for energy demand estimation

## Requirements

- Python 3.8+ (for local development)
- PostgreSQL 12+ with PostGIS extension (for local development)
- Docker and Docker Compose (recommended for deployment)

## Setup with Docker (Recommended)

1. **Clone the repository**:

```bash
git clone <repository-url>
cd energy_model
```

2. **Setup environment variables**:

Copy the `.env.example` file to `.env` and update the configuration:

```bash
cp .env.example .env
# Edit .env file with your desired PostgreSQL credentials
```

3. **Start the services**:

```bash
# For production
docker-compose up -d

# For development (includes Martin and PgAdmin)
docker-compose -f docker-compose.dev.yml up -d
```

4. **Import data**:

```bash
# Import all data
./scripts/docker_import_data.sh --recreate-tables

# Import specific batches
./scripts/docker_import_data.sh --batch-start 1 --batch-end 10

# Import administrative boundaries and statistics
./import_admin_stats.sh
```

5. **Access the services**:

- API: http://localhost:8008 (Swagger UI at http://localhost:8008/docs)
- Martin vector tiles (dev only): http://localhost:3015
- PgAdmin (dev only): http://localhost:5050 (login with admin@example.com / admin)

## Local Setup (Without Docker)

1. **Create a virtual environment**:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:

```bash
pip install -r requirements.txt
```

3. **Setup environment variables**:

Copy the `.env.example` file to `.env` and update the configuration:

```bash
cp .env.example .env
# Edit .env file with your PostgreSQL credentials
```

4. **Create the database**:

```bash
# Create a PostgreSQL database
createdb -U postgres energy_model

# Apply migrations
alembic upgrade head
```

5. **Import data**:

```bash
# Import all data
python scripts/import_buildings_to_db.py --recreate-tables

# Import specific batches
python scripts/import_buildings_to_db.py --batch-start 1 --batch-end 10
```

6. **Run the API**:

```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Buildings API
- `GET /api/v1/buildings/`: List buildings with filtering options
- `GET /api/v1/buildings/bbox`: Query buildings within a bounding box
- `GET /api/v1/buildings/statistics`: Get aggregated statistics about buildings

### Metrics API
- `GET /api/v1/metrics/national`: Get national-level electrification statistics with confidence thresholds
- `GET /api/v1/metrics/regions`: List all regions with basic statistics
- `GET /api/v1/metrics/region/{region_name}`: Get detailed metrics for a specific region
- `GET /api/v1/metrics/priority-zones`: Get areas with high priority for electrification, verification, or high energy demand
- `GET /api/v1/metrics/uncertainty-analysis`: Get communes categorized by energy consumption uncertainty levels

## Administrative Statistics

The system includes a comprehensive administrative statistics module that:

1. **Hierarchical Visualization**: Displays statistics at various administrative levels (regions, departments, arrondissements, communes)
2. **Multiple Metrics**: Shows electrification rates, building density, high-confidence statistics, and more
3. **Color-coded Maps**: Visualizes data using color gradients for easy interpretation
4. **Interactive UI**: Allows toggling visibility, changing administrative levels, and viewing detailed information

To set up administrative statistics:
```bash
./import_admin_stats.sh
```

This will:
- Import administrative boundary data from GeoJSON APIs
- Calculate statistics for each administrative level
- Create database views for vector tile rendering
- Restart the Martin tile server

## Integration with Martin and MapLibre

This backend is designed to work with:

- [Martin](https://github.com/maplibre/martin) for serving vector tiles from PostGIS
- [MapLibre GL JS](https://maplibre.org/maplibre-gl-js-docs/api/) for rendering

When using the dev Docker Compose setup, Martin is automatically configured to connect to the PostgreSQL database. You can access vector tiles at:

http://localhost:3015/tiles/{table_name}/{z}/{x}/{y}.pbf

For example, to access building data:
http://localhost:3015/tiles/buildings_energy/{z}/{x}/{y}.pbf

## Documentation

For detailed information on API usage and data visualization:

- [Frontend Developer Guide](docs/frontend_developer_guide.md): Comprehensive guide for frontend developers on using the API and visualizing data
- [API Reference](http://localhost:8008/docs): Full API documentation (available when server is running)
- [Database Schema](docs/database_schema.md): Overview of database structure and relationships
