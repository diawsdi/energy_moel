#!/usr/bin/env python3
"""
Simple script to test database connection.
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_connection():
    """Test database connection with different connection strings."""
    
    # Get connection parameters from environment variables
    db_user = os.environ.get("POSTGRES_USER", "postgres")
    db_password = os.environ.get("POSTGRES_PASSWORD", "password")
    db_host = "localhost"  # Use localhost for local connections
    db_port = "5438"  # Use port 5438 for local connections
    db_name = os.environ.get("POSTGRES_DB", "energy_model")
    
    # Test different connection strings
    connection_strings = [
        f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}",
        f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}",
        f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}//{db_name}",
        f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}//{db_name}"
    ]
    
    success = False
    
    for i, conn_str in enumerate(connection_strings, 1):
        logger.info(f"Testing connection string {i}: {conn_str}")
        
        try:
            # Create engine
            engine = create_engine(conn_str)
            
            # Try to connect
            with engine.connect() as conn:
                # Execute a simple query
                result = conn.execute(text("SELECT 1"))
                value = result.scalar()
                logger.info(f"Connection successful! Query result: {value}")
                
                # Get database version
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                logger.info(f"Database version: {version}")
                
                # List tables
                result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
                tables = [row[0] for row in result]
                logger.info(f"Tables in database: {', '.join(tables)}")
                
                success = True
                logger.info(f"Connection string {i} works: {conn_str}")
                break
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
    
    if success:
        logger.info("Database connection test completed successfully.")
    else:
        logger.error("All connection attempts failed.")
        
if __name__ == "__main__":
    test_connection()
