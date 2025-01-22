"""Wallet database operations."""

import json
from typing import Dict, Optional
from sqlalchemy import text

from agent_backend.db.setup import get_engine

def save_wallet(wallet_id: str, data: Dict) -> None:
    """Save wallet data to the database."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(
            text("INSERT OR REPLACE INTO wallets (id, data) VALUES (:id, :data)"),
            {"id": wallet_id, "data": json.dumps(data)}
        )
        conn.commit()

def get_wallet(wallet_id: str) -> Optional[Dict]:
    """Get wallet data from the database."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT data FROM wallets WHERE id = :id"),
            {"id": wallet_id}
        ).first()
        
        if result:
            return json.loads(result[0])
        return None 