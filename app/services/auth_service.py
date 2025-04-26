from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import verify_password, create_access_token
from app.core.dependencies import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def authenticate_user(username: str, password: str, db: Session):
    user = db.query(User).filter(User.email == username).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return user

def login_user(username: str, password: str, db: Session):
    user = authenticate_user(username, password, db)
    return {"access_token": create_access_token(user.email), "token_type": "bearer"}

def generate_otp():
    return random.randint(100000, 999999)

def verify_otp(user_id: int, otp: int):
    # Logic to verify OTP (e.g., via Redis)
    pass
async def linkedin_login(access_token: str):
    url = f"https://api.linkedin.com/v2/me?oauth2_access_token={access_token}"
    response = requests.get(url)
    return response.json()