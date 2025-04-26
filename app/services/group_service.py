from sqlalchemy.orm import Session
from app.models.group import Group
from app.models.user import User
from app.schemas.group import GroupCreateSchema

def create_group(group_data: GroupCreateSchema, db: Session):
    group = Group(**group_data.dict())
    db.add(group)
    db.commit()
    db.refresh(group)
    return group

def add_user_to_group(group_id: int, user_id: int, db: Session):
    group = db.query(Group).filter(Group.id == group_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    if not group or not user:
        raise ValueError("Group or User not found")
    user.group_id = group.id
    db.commit()
    return group

def delete_group(group_id: int, db: Session):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise ValueError("Group not found")
    db.delete(group)
    db.commit()
def send_group_invitation(group_id: int, email: str):
    link = generate_invite_link(group_id)
    send_email(email, f"Join the group using this link: {link}")

