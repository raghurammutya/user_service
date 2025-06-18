# Import security utilities from shared_architecture
from shared_architecture.auth.jwt_manager import JWTManager
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import AppConfig

# Password hashing configuration (keep service-specific)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against its hashed version.
    """
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    """
    Hashes a plain password using bcrypt.
    """
    return pwd_context.hash(password)

def create_access_token(subject: str, expires_delta: timedelta = timedelta(hours=1)) -> str:
    """
    Creates a JWT access token for the given subject (e.g., user email).
    Note: For now keeping simple JWT creation. Can be migrated to shared JWT manager
    when Keycloak configuration is available.
    """
    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": subject,
        "exp": expire,
    }
    return jwt.encode(payload, AppConfig.jwt_secret_key, algorithm=AppConfig.jwt_algorithm)

# TODO: Migrate to shared JWT manager when Keycloak config is available
# jwt_manager = JWTManager(
#     keycloak_url=AppConfig.keycloak_url,
#     realm=AppConfig.keycloak_realm, 
#     client_id=AppConfig.keycloak_client_id
# )