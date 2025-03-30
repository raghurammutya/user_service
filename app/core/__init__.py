# Initialize core utilities and configurations
from .config import AppConfig
from .dependencies import get_db
from .events import startup_event, shutdown_event
from .security import verify_password, hash_password, create_access_token
from .logging import setup_logging

# Expose modules for convenient imports
__all__ = [
    "AppConfig",
    "get_db",
    "startup_event",
    "shutdown_event",
    "verify_password",
    "hash_password",
    "create_access_token",
    "setup_logging",
]