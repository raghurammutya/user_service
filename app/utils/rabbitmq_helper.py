import aio_pika

async def publish_message(rabbitmq_conn, exchange_name: str, routing_key: str, message_body: str):
    """
    Publish a message to a RabbitMQ exchange with a specified routing key.
    """
    channel = await rabbitmq_conn.channel()
    exchange = await channel.declare_exchange(exchange_name, aio_pika.ExchangeType.TOPIC)
    message = aio_pika.Message(body=message_body.encode())
    await exchange.publish(message, routing_key=routing_key)