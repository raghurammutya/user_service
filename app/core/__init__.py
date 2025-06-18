# Initialize core utilities and configurations
from .config import AppConfig
from .dependencies import get_db

# Check what modules exist and only import available ones
try:
    from .security import verify_password, hash_password, create_access_token
    _security_available = True
except ImportError:
    _security_available = False

# Expose modules for convenient imports
__all__ = [
    "AppConfig",
    "get_db",
]

if _security_available:
    __all__.extend(["verify_password", "hash_password", "create_access_token"])