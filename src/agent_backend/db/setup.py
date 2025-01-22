"""Database setup and initialization."""

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from agent_backend.db.config import get_database_url, get_engine_options

logger = logging.getLogger(__name__)

def get_engine() -> Engine:
    """Get SQLAlchemy engine with appropriate configuration."""
    url = get_database_url()
    options = get_engine_options()
    return create_engine(url, **options)

def setup_database() -> None:
    """Set up the database tables."""
    try:
        engine = get_engine()
        
        # Create tables using SQLAlchemy
        with engine.connect() as conn:
            # Create wallet info table with security metadata
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS wallet_info (
                    wallet_id VARCHAR(255) PRIMARY KEY,
                    info JSONB NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    validation_count INTEGER DEFAULT 1,
                    CONSTRAINT valid_json CHECK (info IS NOT NULL)
                )
            """))
            
            # Create index on updated_at for efficient queries
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_wallet_updated 
                ON wallet_info(updated_at)
            """))
            
            conn.commit()
            logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to set up database: {str(e)}")
        raise