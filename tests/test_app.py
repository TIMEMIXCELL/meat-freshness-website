import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index(client):
    """Test the index page returns a 200 status code"""
    response = client.get('/')
    assert response.status_code == 200

def test_classify_no_image(client):
    """Test the classify route with no image input"""
    response = client.post('/classify', data={})
    assert b"No file or image captured" in response.data
