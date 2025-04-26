import os
from shared_architecture.models.config_map import ConfigMap

class AppConfig:
    """
    Reads configuration parameters from the environment or ConfigMap.
    ConfigMap is used for production, while `.env` is used for local development/testing.
    """
    rabbitmq_url = os.getenv("RABBITMQ_URL", ConfigMap.get("RABBITMQ_URL"))
    db_url = os.getenv("TIMESCALEDB_URL", ConfigMap.get("TIMESCALEDB_URL"))
    redis_url = os.getenv("REDIS_URL", ConfigMap.get("REDIS_URL"))
    keycloak_url = os.getenv("KEYCLOAK_URL", ConfigMap.get("KEYCLOAK_URL"))
    keycloak_realm = os.getenv("KEYCLOAK_REALM", ConfigMap.get("KEYCLOAK_REALM"))
    keycloak_client_id = os.getenv("KEYCLOAK_CLIENT_ID", ConfigMap.get("KEYCLOAK_CLIENT_ID"))
    jwt_secret_key = os.getenv("JWT_SECRET_KEY", ConfigMap.get("JWT_SECRET_KEY"))
    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://user:password@localhost:5672/")