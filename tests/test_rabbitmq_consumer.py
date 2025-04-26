import pytest
from app.messaging.rabbitmq_consumer import consume_messages

@pytest.mark.asyncio
async def test_consume_messages():
    async def mock_process_message_callback(message_body):
        assert message_body == "Test Message"
    
    await consume_messages("my_exchange", "my_routing_key", mock_process_message_callback)