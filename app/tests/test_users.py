from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_user():
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone_number": "+12345678901"
    }
    response = client.post("/users/", json=payload)
    assert response.status_code == 200
    assert response.json()["first_name"] == "John"

def test_get_user():
    user_id = 1
    response = client.get(f"/users/{user_id}/")
    assert response.status_code == 200
    assert response.json()["id"] == user_id