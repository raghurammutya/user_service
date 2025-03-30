from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from app.core.config import AppConfig

# Password hashing configuration
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
    """
    expire = datetime.utcnow() + expires_delta
    payload = {
        "sub": subject,
        "exp": expire,
    }
    return jwt.encode(payload, AppConfig.jwt_secret_key, algorithm=AppConfig.jwt_algorithm)