"""NFT database operations."""

import sqlite3
import logging
from typing import List

def add_nft(address: str) -> None:
    """Add an NFT address to the database."""
    try:
        conn = sqlite3.connect('agent.db')
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO nfts (address) VALUES (?)', (address,))
        conn.commit()
    except Exception as e:
        logging.error(f"Error adding NFT: {str(e)}")
        raise
    finally:
        conn.close()

def get_nfts() -> List[str]:
    """Get all NFT addresses from the database."""
    try:
        conn = sqlite3.connect('agent.db')
        cursor = conn.cursor()
        cursor.execute('SELECT address FROM nfts')
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logging.error(f"Error getting NFTs: {str(e)}")
        raise
    finally:
        conn.close()