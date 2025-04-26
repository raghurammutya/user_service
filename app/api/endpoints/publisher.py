from fastapi import APIRouter, HTTPException
from app.messaging.rabbitmq_publisher import publish_message

router = APIRouter()

@router.post("/publish/")
async def publish(data: dict):
    try:
        await publish_message("my_exchange", "my_routing_key", data["message"])
        return {"status": "Message published"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))