# Use shared_architecture RabbitMQ utilities
from shared_architecture.utils.data_adapter_rabbitmq import RabbitMQDataAdapter
from shared_architecture.connections.rabbitmq_client import get_rabbitmq_connection
from app.core.config import settings
import asyncio
import aio_pika

async def consume_messages(exchange_name: str, routing_key: str, process_message_callback):
    """
    Consumes messages using shared_architecture RabbitMQ connection.
    """
    try:
        # Use shared connection manager
        connection = await get_rabbitmq_connection()
        
        channel = await connection.channel()
        exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.TOPIC)
        queue = await channel.declare_queue(exclusive=True)
        await queue.bind(exchange, routing_key)

        async for message in queue:
            async with message.process():
                await process_message_callback(message.body.decode())
                
    except Exception as e:
        from shared_architecture.utils.logging_utils import log_exception
        log_exception(f"Error consuming messages: {e}")
        raise

# Alternative: Use data adapter for structured consumption
async def consume_with_adapter(routing_key: str, callback):
    """
    Consume messages using shared RabbitMQ data adapter.
    """
    adapter = RabbitMQDataAdapter()
    await adapter.consume_data(routing_key, callback)