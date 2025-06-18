# Use shared_architecture RabbitMQ utilities
from shared_architecture.utils.rabbitmq_helper import publish_message as shared_publish
from shared_architecture.utils.data_adapter_rabbitmq import RabbitMQDataAdapter
from app.core.config import settings
import asyncio

# Use the shared publish_message function
async def publish_message(exchange_name: str, routing_key: str, message_body: str):
    """
    Publishes a message using shared_architecture RabbitMQ helper.
    """
    # For async version, we can use the data adapter
    adapter = RabbitMQDataAdapter()
    await adapter.publish_data(routing_key, {"message": message_body})

# Alternative: Use sync version from shared helper
def publish_message_sync(queue_name: str, message_body: str):
    """
    Publishes a message using shared_architecture sync RabbitMQ helper.
    """
    shared_publish(
        rabbitmq_url=settings.rabbitmq_url,
        queue_name=queue_name,
        message=message_body
    )