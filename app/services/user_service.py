from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreateSchema, UserUpdateSchema

def create_user(user_data: UserCreateSchema, db: Session):
    user = User(**user_data.dict())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user(user_id: int, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")
    return user

def update_user(user_id: int, user_data: UserUpdateSchema, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")
    for key, value in user_data.dict(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

def delete_user(user_id: int, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")
    db.delete(user)
    db.commit()

def search_users(search_term: str, db: Session):
    return db.query(User).filter(User.first_name.ilike(f"%{search_term}%")).all()

def delete_user_data(user_id: int, db: Session):
    # Delete or anonymize all data related to the user
    pass