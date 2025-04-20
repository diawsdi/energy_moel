#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Apply migrations
echo "Applying database migrations..."
# Commented out for initial setup since migrations are causing issues
# alembic upgrade head

# Start the API server
echo "Starting FastAPI server..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 