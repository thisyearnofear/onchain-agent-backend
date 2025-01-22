"""Database operations for wallet management."""

import logging
import json
from typing import Optional, Dict, Any
from sqlalchemy import text

from agent_backend.db.setup import get_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_wallet_info(wallet_id: str, wallet_info: Dict[str, Any]) -> None:
    """Save wallet information to database."""
    engine = get_engine()
    
    try:
        # Convert wallet info to JSON string
        wallet_json = json.dumps(wallet_info)
        
        with engine.connect() as conn:
            # Check if wallet exists
            result = conn.execute(
                text("SELECT wallet_id FROM wallet_info WHERE wallet_id = :wallet_id"),
                {"wallet_id": wallet_id}
            ).fetchone()
            
            if result:
                # Update existing wallet
                conn.execute(
                    text("""
                    UPDATE wallet_info 
                    SET info = :info,
                        updated_at = NOW(),
                        validation_count = validation_count + 1
                    WHERE wallet_id = :wallet_id
                    """),
                    {"info": wallet_json, "wallet_id": wallet_id}
                )
            else:
                # Insert new wallet
                conn.execute(
                    text("""
                    INSERT INTO wallet_info (wallet_id, info, created_at, updated_at, validation_count)
                    VALUES (:wallet_id, :info, NOW(), NOW(), 1)
                    """),
                    {"wallet_id": wallet_id, "info": wallet_json}
                )
            
            conn.commit()
            logger.info(f"Saved wallet info for {wallet_id}")
        
    except Exception as e:
        logger.error(f"Failed to save wallet info: {str(e)}")
        raise

def get_wallet_info(wallet_id: str) -> Optional[Dict[str, Any]]:
    """Get wallet information from database."""
    engine = get_engine()
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                SELECT info, created_at, updated_at, validation_count
                FROM wallet_info 
                WHERE wallet_id = :wallet_id
                """),
                {"wallet_id": wallet_id}
            ).fetchone()
            
            if result:
                info, created_at, updated_at, validation_count = result
                wallet_info = json.loads(info)
                # Add metadata
                wallet_info.update({
                    "created_at": created_at.isoformat(),
                    "last_validated": updated_at.isoformat(),
                    "validation_count": validation_count
                })
                return wallet_info
            
            return None
            
    except Exception as e:
        logger.error(f"Failed to get wallet info: {str(e)}")
        raise