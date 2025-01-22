"""Database operations for wallet management."""

import sqlite3
from typing import Optional, Dict, Any
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_wallet_info(wallet_id: str, wallet_data: Dict[str, Any]) -> None:
    """
    Save or update wallet information in the database.
    Args:
        wallet_id: The ID of the wallet
        wallet_data: Dictionary containing wallet data including seed if available
    """
    try:
        with sqlite3.connect("agent.db") as conn:
            cursor = conn.cursor()
            
            # Convert wallet data to JSON string
            data_json = json.dumps(wallet_data)
            
            # Insert or replace wallet info
            cursor.execute(
                "INSERT OR REPLACE INTO wallets (id, data) VALUES (?, ?)",
                (wallet_id, data_json)
            )
            
            conn.commit()
            logger.info(f"Successfully saved wallet info for ID: {wallet_id}")
                
    except Exception as e:
        logger.error(f"Error saving wallet info: {str(e)}")
        raise

def get_wallet_info() -> Optional[Dict[str, Any]]:
    """
    Retrieve wallet information from the database.
    Returns:
        Dictionary containing wallet data if found, None otherwise
    """
    try:
        with sqlite3.connect("agent.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, data FROM wallets LIMIT 1")
            result = cursor.fetchone()
            
            if result:
                wallet_id, data_json = result
                wallet_data = json.loads(data_json)
                wallet_data['id'] = wallet_id
                return wallet_data
            
            return None
                
    except Exception as e:
        logger.error(f"Error retrieving wallet info: {str(e)}")
        return None