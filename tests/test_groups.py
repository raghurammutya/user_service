from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_group():
    payload = {
        "name": "Family Group",
        "owner_id": 1
    }
    response = client.post("/groups/", json=payload)
    assert response.status_code == 200
    assert response.json()["name"] == "Family Group"

def test_delete_group():
    group_id = 1
    response = client.delete(f"/groups/{group_id}/")
    assert response.status_code == 200
    assert response.json() == {"message": "Group deleted successfully"}

def test_send_group_invitation():
    payload = {"group_id": 1, "email": "test@example.com"}
    response = client.post("/groups/invite/", json=payload)
    assert response.status_code == 200
    assert "Invite sent successfully" in response.json()["message"]