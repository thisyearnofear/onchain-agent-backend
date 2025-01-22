"""Token database operations."""

import sqlite3
import logging
from typing import List

def add_token(address: str) -> None:
    """Add a token address to the database."""
    try:
        conn = sqlite3.connect('agent.db')
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO tokens (address) VALUES (?)', (address,))
        conn.commit()
    except Exception as e:
        logging.error(f"Error adding token: {str(e)}")
        raise
    finally:
        conn.close()

def get_tokens() -> List[str]:
    """Get all token addresses from the database."""
    try:
        conn = sqlite3.connect('agent.db')
        cursor = conn.cursor()
        cursor.execute('SELECT address FROM tokens')
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logging.error(f"Error getting tokens: {str(e)}")
        raise
    finally:
        conn.close()