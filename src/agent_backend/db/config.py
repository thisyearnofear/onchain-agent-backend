"""Database configuration module."""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_url() -> str:
    """Get the database URL based on the environment."""
    # Check if we're in production
    if os.getenv('ENVIRONMENT') == 'production':
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        host = os.getenv("POSTGRES_HOST", "localhost")
        db = os.getenv("POSTGRES_DB", "onchain_agent")
        return f"postgresql://{user}:{password}@{host}/{db}"
    
    # Development: Use SQLite with the original agent.db file
    return "sqlite:///agent.db"

def get_engine_options() -> dict:
    """Get SQLAlchemy engine options based on the environment."""
    if os.getenv('ENVIRONMENT') == 'production':
        return {
            "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
            "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
            "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "1800")),
        }
    return {} 