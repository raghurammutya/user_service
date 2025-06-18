# Use shared architecture Group model and extend if needed
from shared_architecture.db.models.group import Group as SharedGroup

# For now, use the shared Group model directly
# If you need user_service specific fields, you can extend like this:
# class GroupExtended(SharedGroup):
#     __tablename__ = "groups_extended" 
#     # Add other user_service specific fields

# Use the shared Group model
Group = SharedGroup