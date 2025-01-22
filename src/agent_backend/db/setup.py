"""Database setup and initialization."""

import sqlite3
import logging

def setup():
    """Create the SQLite tables if they don't exist."""
    try:
        conn = sqlite3.connect('agent.db')
        cursor = conn.cursor()

        # Create wallets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wallets (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
        ''')

        # Create tokens table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tokens (
                address TEXT PRIMARY KEY
            )
        ''')

        # Create NFTs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nfts (
                address TEXT PRIMARY KEY
            )
        ''')

        conn.commit()
        logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error setting up database: {str(e)}")
        raise
    finally:
        conn.close()