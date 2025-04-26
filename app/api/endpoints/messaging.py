from fastapi import APIRouter, WebSocket, Depends
from app.messaging.websocket import WebSocketConnectionManager
from app.messaging.rabbitmq_consumer import consume_messages

router = APIRouter()
manager = WebSocketConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Example: Echo received data
            await manager.send_message(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.on_event("startup")
async def start_rabbitmq_consumer():
    """
    Start consuming messages from RabbitMQ and forward them to WebSocket clients.
    """
    async def process_message_callback(message_body: str):
        await manager.send_message(f"New message: {message_body}")

    # Listen to messages from RabbitMQ
    await consume_messages("my_exchange", "my_routing_key", process_message_callback)