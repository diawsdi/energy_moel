# Energy Model Backend

A FastAPI backend for managing and serving energy model data with PostgreSQL/PostGIS spatial database.

## Features

- RESTful API with FastAPI
- PostgreSQL with PostGIS for spatial data storage
- Efficient spatial queries for MapLibre and Martin vector tile rendering
- Batch data loading from GeoPackage files
- Docker Compose setup for easy deployment

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
```

5. **Access the services**:

- API: http://localhost:8000 (Swagger UI at http://localhost:8000/docs)
- Martin vector tiles (dev only): http://localhost:3000
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

- `GET /api/v1/buildings/`: List buildings with filtering options
- `GET /api/v1/buildings/bbox`: Query buildings within a bounding box
- `GET /api/v1/buildings/statistics`: Get aggregated statistics about buildings

## Integration with Martin and MapLibre

This backend is designed to work with:

- [Martin](https://github.com/maplibre/martin) for serving vector tiles from PostGIS
- [MapLibre GL JS](https://maplibre.org/maplibre-gl-js-docs/api/) for rendering

When using the dev Docker Compose setup, Martin is automatically configured to connect to the PostgreSQL database. You can access vector tiles at:

http://localhost:3000/tiles/{table_name}/{z}/{x}/{y}.pbf

For example, to access building data:
http://localhost:3000/tiles/buildings_energy/{z}/{x}/{y}.pbf # energy_moel
