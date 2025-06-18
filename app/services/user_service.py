from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from app.models.user import User
from app.schemas.user import UserCreateSchema, UserUpdateSchema

# Import shared architecture utilities
from shared_architecture.utils.error_handler import (
    handle_errors, validate_required_fields, validate_field_types,
    create_error_context
)
from shared_architecture.exceptions.trade_exceptions import (
    ValidationException, DatabaseException
)
from shared_architecture.utils.enhanced_logging import get_logger, LoggingContext
from shared_architecture.utils.service_decorators import with_metrics, with_retry
from shared_architecture.resilience.retry_policies import retry_with_exponential_backoff

logger = get_logger(__name__)

@handle_errors("User creation failed")
@with_metrics("user_service_operations", tags={"operation": "create"})
@retry_with_exponential_backoff(max_attempts=3)
async def create_user(user_data: UserCreateSchema, db: Session) -> User:
    """Create a new user with enhanced error handling and validation"""
    
    # Validate required fields using shared validation
    validate_required_fields(
        user_data.dict(), 
        ['first_name', 'last_name', 'email']
    )
    
    # Validate field types
    validate_field_types(user_data.dict(), {
        'first_name': str,
        'last_name': str,
        'email': str
    })
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValidationException(
                "User with this email already exists",
                field_name="email",
                field_value=user_data.email
            )
        
        # Create user
        user = User(**user_data.dict())
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"User created successfully", user_id=user.id, email=user.email)
        return user
        
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseException(
            "Failed to create user in database",
            operation="insert",
            table="users",
            original_exception=e
        )

@handle_errors("User retrieval failed")
@with_metrics("user_service_operations", tags={"operation": "get"})
async def get_user(user_id: int, db: Session) -> User:
    """Get user by ID with enhanced error handling"""
    
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValidationException(
            "User ID must be a positive integer",
            field_name="user_id",
            field_value=user_id
        )
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValidationException(
                f"User with ID {user_id} not found",
                field_name="user_id",
                field_value=user_id
            )
        
        logger.info(f"User retrieved successfully", user_id=user.id)
        return user
        
    except SQLAlchemyError as e:
        raise DatabaseException(
            "Failed to retrieve user from database",
            operation="select",
            table="users",
            original_exception=e
        )

@handle_errors("User update failed")
@with_metrics("user_service_operations", tags={"operation": "update"})
@retry_with_exponential_backoff(max_attempts=3)
async def update_user(user_id: int, user_data: UserUpdateSchema, db: Session) -> User:
    """Update user with enhanced error handling and validation"""
    
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValidationException(
            "User ID must be a positive integer",
            field_name="user_id",
            field_value=user_id
        )
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValidationException(
                f"User with ID {user_id} not found",
                field_name="user_id",
                field_value=user_id
            )
        
        # Update only provided fields
        update_data = user_data.dict(exclude_unset=True)
        if not update_data:
            raise ValidationException("No fields provided for update")
        
        # Check if email is being updated and already exists
        if 'email' in update_data:
            existing_user = db.query(User).filter(
                User.email == update_data['email'],
                User.id != user_id
            ).first()
            if existing_user:
                raise ValidationException(
                    "Email already exists for another user",
                    field_name="email",
                    field_value=update_data['email']
                )
        
        # Apply updates
        for key, value in update_data.items():
            setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"User updated successfully", user_id=user.id, updated_fields=list(update_data.keys()))
        return user
        
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseException(
            "Failed to update user in database",
            operation="update",
            table="users",
            original_exception=e
        )

@handle_errors("User deletion failed")
@with_metrics("user_service_operations", tags={"operation": "delete"})
@retry_with_exponential_backoff(max_attempts=3)
async def delete_user(user_id: int, db: Session) -> None:
    """Delete user with enhanced error handling"""
    
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValidationException(
            "User ID must be a positive integer",
            field_name="user_id",
            field_value=user_id
        )
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValidationException(
                f"User with ID {user_id} not found",
                field_name="user_id",
                field_value=user_id
            )
        
        user_email = user.email  # Store for logging
        db.delete(user)
        db.commit()
        
        logger.info(f"User deleted successfully", user_id=user_id, email=user_email)
        
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseException(
            "Failed to delete user from database",
            operation="delete",
            table="users",
            original_exception=e
        )

@handle_errors("User search failed")
@with_metrics("user_service_operations", tags={"operation": "search"})
async def search_users(search_term: str, db: Session) -> List[User]:
    """Search users with enhanced error handling and validation"""
    
    if not search_term or not isinstance(search_term, str):
        raise ValidationException(
            "Search term must be a non-empty string",
            field_name="search_term",
            field_value=search_term
        )
    
    if len(search_term.strip()) < 2:
        raise ValidationException(
            "Search term must be at least 2 characters long",
            field_name="search_term",
            field_value=search_term
        )
    
    try:
        search_term = search_term.strip()
        users = db.query(User).filter(
            User.first_name.ilike(f"%{search_term}%") |
            User.last_name.ilike(f"%{search_term}%") |
            User.email.ilike(f"%{search_term}%")
        ).limit(50).all()  # Limit results for performance
        
        logger.info(f"User search completed", search_term=search_term, results_count=len(users))
        return users
        
    except SQLAlchemyError as e:
        raise DatabaseException(
            "Failed to search users in database",
            operation="select",
            table="users",
            original_exception=e
        )

@handle_errors("User data deletion failed")
@with_metrics("user_service_operations", tags={"operation": "data_deletion"})
async def delete_user_data(user_id: int, db: Session) -> None:
    """Delete or anonymize all data related to the user (GDPR compliance)"""
    
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValidationException(
            "User ID must be a positive integer",
            field_name="user_id",
            field_value=user_id
        )
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValidationException(
                f"User with ID {user_id} not found",
                field_name="user_id",
                field_value=user_id
            )
        
        # Anonymize user data instead of deleting
        user.first_name = "[DELETED]"
        user.last_name = "[DELETED]"
        user.email = f"deleted_user_{user_id}@deleted.local"
        user.phone_number = None
        
        db.commit()
        
        logger.info(f"User data anonymized for GDPR compliance", user_id=user_id)
        
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseException(
            "Failed to anonymize user data",
            operation="update",
            table="users",
            original_exception=e
        )