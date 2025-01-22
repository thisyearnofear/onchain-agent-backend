"""NFT database operations."""

from typing import List
from sqlalchemy import text

from agent_backend.db.setup import get_engine

def add_nft(address: str) -> None:
    """Add an NFT address to the database."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(
            text("INSERT OR REPLACE INTO nfts (address) VALUES (:address)"),
            {"address": address}
        )
        conn.commit()

def get_nfts() -> List[str]:
    """Get all NFT addresses from the database."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT address FROM nfts"))
        return [row[0] for row in result]