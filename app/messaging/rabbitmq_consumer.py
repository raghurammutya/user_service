import aio_pika
from app.core.config import AppConfig

async def consume_messages(exchange_name: str, routing_key: str, process_message_callback):
    """
    Consumes messages from the RabbitMQ exchange with a specific routing key.
    """
    connection = await aio_pika.connect_robust(AppConfig.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.TOPIC)
        queue = await channel.declare_queue(exclusive=True)
        await queue.bind(exchange, routing_key)

        async for message in queue:
            async with message.process():
                await process_message_callback(message.body.decode())