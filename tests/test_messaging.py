from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_publish_message():
    response = client.post("/publish/", json={"message": "Hello RabbitMQ!"})
    assert response.status_code == 200
    assert response.json()["status"] == "Message published"

def test_websocket_communication():
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text("Hello WebSocket!")
        data = websocket.receive_text()
        assert data == "Message received: Hello WebSocket!"