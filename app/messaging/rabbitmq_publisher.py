import aio_pika
from app.core.config import AppConfig

async def publish_message(exchange_name: str, routing_key: str, message_body: str):
    """
    Publishes a message to the RabbitMQ exchange with a specific routing key.
    """
    connection = await aio_pika.connect_robust(AppConfig.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.TOPIC)
        message = aio_pika.Message(body=message_body.encode())
        await exchange.publish(message, routing_key=routing_key)