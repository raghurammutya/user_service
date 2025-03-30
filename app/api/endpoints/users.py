from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreateSchema, UserResponseSchema
from app.services.user_service import create_user
from app.core.dependencies import get_db

router = APIRouter()

@router.post("/", response_model=UserResponseSchema)
def register_user(user_data: UserCreateSchema, db: Session = Depends(get_db)):
    return create_user(user_data, db)