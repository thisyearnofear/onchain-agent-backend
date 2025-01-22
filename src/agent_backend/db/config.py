"""Database configuration module."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url() -> str:
    """Get the database URL based on the environment."""
    # Check if we're in production (Render sets this automatically)
    if os.getenv('RENDER'):
        user = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")
        host = os.getenv("POSTGRES_HOST")
        db = os.getenv("POSTGRES_DB")
        
        if not all([user, password, host, db]):
            raise ValueError("Missing required database configuration. Please set POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, and POSTGRES_DB")
            
        # Construct the URL without trying to parse host/port
        return f"postgresql://{user}:{password}@{host}/{db}"
    
    # Development: Use SQLite with the original agent.db file
    return "sqlite:///agent.db"

def get_engine_options() -> dict:
    """Get SQLAlchemy engine options based on the environment."""
    if os.getenv('RENDER'):
        return {
            "pool_size": 3,  # Reduced pool size for Render free tier
            "max_overflow": 5,  # Reduced max overflow
            "pool_timeout": 30,
            "pool_recycle": 1800,
            "pool_pre_ping": True,  # Enable connection health checks
        }
    return {} 