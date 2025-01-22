"""Database models for the application."""

from datetime import datetime
from typing import Dict, Any
import json

from sqlalchemy import Column, String, DateTime, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Wallet(Base):
    """Wallet model for storing CDP wallet information."""
    __tablename__ = 'wallets'

    id = Column(String, primary_key=True)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def network_id(self) -> str:
        """Get the network ID from the wallet data."""
        return self.data.get('network_id')

    @property
    def default_address(self) -> str:
        """Get the default address from the wallet data."""
        return self.data.get('default_address')

    def to_dict(self) -> Dict[str, Any]:
        """Convert the wallet to a dictionary."""
        return {
            'id': self.id,
            'data': self.data,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Token(Base):
    """Token model for storing deployed token information."""
    __tablename__ = 'tokens'

    address = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the token to a dictionary."""
        return {
            'address': self.address,
            'name': self.name,
            'symbol': self.symbol,
            'created_at': self.created_at.isoformat()
        }

class NFT(Base):
    """NFT model for storing deployed NFT information."""
    __tablename__ = 'nfts'

    address = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the NFT to a dictionary."""
        return {
            'address': self.address,
            'name': self.name,
            'symbol': self.symbol,
            'created_at': self.created_at.isoformat()
        }

def init_db(database_url: str) -> sessionmaker:
    """Initialize the database connection."""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine) 