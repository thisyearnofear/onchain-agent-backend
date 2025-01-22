"""Database setup and initialization."""

import logging
import sqlite3
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from agent_backend.db.config import get_database_url, get_engine_options

logger = logging.getLogger(__name__)

def get_engine() -> Engine:
    """Get SQLAlchemy engine with appropriate configuration."""
    url = get_database_url()
    options = get_engine_options()
    return create_engine(url, **options)

def setup() -> None:
    """Set up database tables."""
    try:
        engine = get_engine()
        
        # Create tables
        with engine.connect() as conn:
            # Create wallets table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS wallets (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL
                )
            """))
            
            # Create tokens table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tokens (
                    address TEXT PRIMARY KEY
                )
            """))
            
            # Create nfts table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS nfts (
                    address TEXT PRIMARY KEY
                )
            """))
            
            conn.commit()
            
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        raise