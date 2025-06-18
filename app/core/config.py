import os
from shared_architecture.config.config_loader import config_loader

class AppConfig:
    """
    Reads configuration parameters from the shared architecture config system.
    Uses the new hierarchical configuration: environment variables -> service config -> shared config -> common config
    """
    
    @property
    def rabbitmq_url(self) -> str:
        return config_loader.get("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/", scope="all")
    
    @property
    def db_url(self) -> str:
        return config_loader.get("TIMESCALEDB_URL", "postgresql://tradmin:tradpass@timescaledb:5432/tradingdb", scope="all")
    
    @property
    def redis_url(self) -> str:
        return config_loader.get("REDIS_URL", "redis://redis:6379/0", scope="all")
    
    @property
    def keycloak_url(self) -> str:
        return config_loader.get("KEYCLOAK_URL", "http://keycloak:8080", scope="all")
    
    @property
    def keycloak_realm(self) -> str:
        return config_loader.get("KEYCLOAK_REALM", "stocksblitz", scope="all")
    
    @property
    def keycloak_client_id(self) -> str:
        return config_loader.get("KEYCLOAK_CLIENT_ID", "user-service", scope="all")
    
    @property
    def jwt_secret_key(self) -> str:
        return config_loader.get("JWT_SECRET_KEY", "your-secret-key-change-in-production", scope="all")
    
    @property
    def jwt_algorithm(self) -> str:
        return config_loader.get("JWT_ALGORITHM", "HS256", scope="all")
    
    @property
    def uvicorn_port(self) -> int:
        return int(config_loader.get("UVICORN_PORT", "8002", scope="all"))
    
    @property
    def debug_mode(self) -> bool:
        return config_loader.get("DEBUG_MODE", "false", scope="all").lower() == "true"

# Global settings instance
settings = AppConfig()