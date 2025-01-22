import pytest
from agent_backend.index import app
from agent_backend.db.setup import setup

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        setup()  # Setup test database
        yield client

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['database'] == 'connected'
    assert 'timestamp' in data

def test_chat_validation(client):
    """Test chat endpoint validation."""
    # Test missing input
    response = client.post('/api/chat', json={
        'conversation_id': 'test-123'
    })
    assert response.status_code == 400
    
    # Test missing conversation_id
    response = client.post('/api/chat', json={
        'input': 'Hello'
    })
    assert response.status_code == 400
    
    # Test empty input
    response = client.post('/api/chat', json={
        'input': '',
        'conversation_id': 'test-123'
    })
    assert response.status_code == 400 