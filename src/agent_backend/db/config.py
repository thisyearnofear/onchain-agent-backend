"""Database configuration."""

import os
from typing import Dict, Any
from urllib.parse import urlparse

def get_database_url() -> str:
    """Get database URL from environment variables."""
    # First try Render's internal database URL
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Parse the URL to handle any special characters in password
        parsed = urlparse(database_url)
        # Reconstruct the URL with proper escaping
        return f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port or 5432}{parsed.path}"
        
    # Fallback to constructing URL from individual components
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "onchain_agent")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"

def get_engine_options() -> Dict[str, Any]:
    """Get SQLAlchemy engine options."""
    return {
        "pool_pre_ping": True,  # Enable connection health checks
        "pool_size": 5,  # Set a reasonable pool size
        "max_overflow": 10,  # Allow some overflow connections
        "pool_timeout": 30,  # Connection timeout in seconds
        "pool_recycle": 1800,  # Recycle connections every 30 minutes
        "echo": True,  # Enable SQL query logging for debugging
    } 