#!/usr/bin/env python3
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_PARAMS = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5438"),
    "database": os.environ.get("DB_NAME", "energy_model"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "password")
}

def check_villages():
    """Check the imported village points data."""
    # Create database engine
    db_url = f"postgresql://{DB_PARAMS['user']}:{DB_PARAMS['password']}@{DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['database']}"
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        # Get total count
        result = conn.execute(text("SELECT COUNT(*) FROM village_points")).fetchone()
        print(f"Total villages: {result[0]}")
        
        # Sample some villages with their communes
        print("\nSample villages:")
        result = conn.execute(text("""
        SELECT v.name, v.commune_id, ab.name as commune_name
        FROM village_points v
        JOIN administrative_boundaries ab ON v.commune_id = ab.id
        LIMIT 5
        """))
        
        for row in result:
            print(f"Village: {row[0]}, Commune: {row[2]} (ID: {row[1]})")

if __name__ == "__main__":
    check_villages() 