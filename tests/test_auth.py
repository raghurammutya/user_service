from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_user():
    payload = {
        "username": "john.doe@example.com",
        "password": "securepassword"
    }
    response = client.post("/auth/login", data=payload)
    assert response.status_code == 200
    assert "access_token" in response.json()