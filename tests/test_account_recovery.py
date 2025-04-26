from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_send_password_reset_email():
    payload = {"email": "test@example.com"}
    response = client.post("/account/recovery/", json=payload)
    assert response.status_code == 200
    assert "Password reset email sent" in response.json()["message"]