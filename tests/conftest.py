import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test environment variables
os.environ['ENVIRONMENT'] = 'test'
os.environ['POSTGRES_USER'] = 'postgres'
os.environ['POSTGRES_PASSWORD'] = 'postgres'
os.environ['POSTGRES_DB'] = 'onchain_agent_test'
os.environ['POSTGRES_HOST'] = 'localhost'

# Mock CDP and OpenAI credentials for testing
os.environ['CDP_API_KEY_NAME'] = 'test-key'
os.environ['CDP_API_KEY_PRIVATE_KEY'] = 'test-private-key'
os.environ['OPENAI_API_KEY'] = 'test-openai-key'

@pytest.fixture(scope='session')
def test_db():
    """Create test database connection."""
    db_url = f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}/{os.environ['POSTGRES_DB']}"
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session() 