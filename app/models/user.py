# Use shared architecture User model and extend if needed
from shared_architecture.db.models.user import User as SharedUser
from sqlalchemy import Column, String
from shared_architecture.enums import UserRole

# For now, use the shared User model directly
# If you need user_service specific fields, you can extend like this:
# class UserExtended(SharedUser):
#     __tablename__ = "users_extended" 
#     phone_number = Column(String, unique=True)
#     # Add other user_service specific fields

# Use the shared User model
User = SharedUser
    
