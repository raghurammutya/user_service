# Import User schemas from shared_architecture
from shared_architecture.schemas.user import (
    UserCreateSchema,
    UserUpdateSchema, 
    UserResponseSchema
)

# Re-export for backward compatibility
__all__ = ["UserCreateSchema", "UserUpdateSchema", "UserResponseSchema"]