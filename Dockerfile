FROM python:3.10-slim

WORKDIR /app/

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.local/bin:${PATH}"

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make sure required packages are installed
RUN pip install --no-cache-dir alembic uvicorn fastapi

# Create a non-root user and set permissions
RUN useradd -m appuser && chown -R appuser:appuser /app/
USER appuser

# Copy project files
COPY --chown=appuser:appuser . .

# Make scripts executable
RUN chmod +x scripts/run_api.sh
RUN chmod +x scripts/run_api_with_migrations.sh
RUN chmod +x scripts/import_buildings_to_db.py

# Expose the port
EXPOSE 8000

# Command to run when container starts
CMD ["bash", "scripts/run_api_with_migrations.sh"] 