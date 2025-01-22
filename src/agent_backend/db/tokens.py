"""Token database operations."""

from typing import List
from sqlalchemy import text

from agent_backend.db.setup import get_engine

def add_token(address: str) -> None:
    """Add a token address to the database."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(
            text("INSERT OR REPLACE INTO tokens (address) VALUES (:address)"),
            {"address": address}
        )
        conn.commit()

def get_tokens() -> List[str]:
    """Get all token addresses from the database."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT address FROM tokens"))
        return [row[0] for row in result]