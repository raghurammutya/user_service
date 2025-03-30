from sqlalchemy.orm import sessionmaker
from redis import Redis
import aio_pika
from shared_architecture.db import TimescaleConnectionManager

class ConnectionManager:
    """
    Manages shared connections for TimescaleDB, Redis, and RabbitMQ.
    """
    _timescaledb_conn = None
    _redis_conn = None
    _rabbitmq_conn = None

    @classmethod
    def initialize(cls):
        cls._timescaledb_conn = TimescaleConnectionManager().get_session()
        cls._redis_conn = Redis(host="redis-host", port=6379)
        cls._rabbitmq_conn = aio_pika.connect_robust("amqp://user:pass@rabbitmq-host")

    @classmethod
    def get_timescaledb_session(cls):
        return cls._timescaledb_conn

    @classmethod
    def get_redis_connection(cls):
        return cls._redis_conn

    @classmethod
    async def get_rabbitmq_connection(cls):
        return await cls._rabbitmq_conn

    @classmethod
    def close(cls):
        if cls._timescaledb_conn:
            cls._timescaledb_conn.close()
        if cls._redis_conn:
            cls._redis_conn.close()
        if cls._rabbitmq_conn:
            cls._rabbitmq_conn.close()