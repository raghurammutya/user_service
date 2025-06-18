from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.models.user import User
from app.schemas.user import UserCreateSchema, UserResponseSchema, UserUpdateSchema
from app.services.user_service import (
    create_user, get_user, update_user, delete_user, search_users
)
from app.core.dependencies import get_db

# Import shared architecture utilities
# Temporarily disabled due to import issue in shared_architecture
# from shared_architecture.utils.service_decorators import (
#     api_endpoint, with_metrics, with_validation
# )
from shared_architecture.utils.error_handler import handle_errors
from shared_architecture.utils.enhanced_logging import get_logger, LoggingContext

router = APIRouter()
logger = get_logger(__name__)

@router.post("/", response_model=UserResponseSchema)
# @api_endpoint(
#     rate_limit="100/minute",
#     timeout=30.0,
#     metrics_name="user_creation"
# )
@handle_errors("User registration failed")
async def register_user(user_data: UserCreateSchema, db: Session = Depends(get_db)):
    """Register a new user with enhanced error handling and metrics"""
    with LoggingContext(operation="user_registration", email=user_data.email):
        logger.info("Creating new user")
        return await create_user(user_data, db)

@router.get("/{user_id}", response_model=UserResponseSchema)
# @api_endpoint(
#     rate_limit="200/minute",
#     timeout=15.0,
#     metrics_name="user_retrieval"
# )
@handle_errors("User retrieval failed")
async def get_user_by_id(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID with enhanced error handling"""
    with LoggingContext(operation="user_retrieval", user_id=str(user_id)):
        logger.info(f"Retrieving user {user_id}")
        return await get_user(user_id, db)

@router.put("/{user_id}", response_model=UserResponseSchema)
# @api_endpoint(
#     rate_limit="50/minute",
#     timeout=30.0,
#     metrics_name="user_update"
# )
@handle_errors("User update failed")
async def update_user_by_id(
    user_id: int,
    user_data: UserUpdateSchema,
    db: Session = Depends(get_db)
):
    """Update user with enhanced error handling and metrics"""
    with LoggingContext(operation="user_update", user_id=str(user_id)):
        logger.info(f"Updating user {user_id}")
        return await update_user(user_id, user_data, db)

@router.delete("/{user_id}")
# @api_endpoint(
#     rate_limit="10/minute",
#     timeout=30.0,
#     metrics_name="user_deletion"
# )
@handle_errors("User deletion failed")
async def delete_user_by_id(user_id: int, db: Session = Depends(get_db)):
    """Delete user with enhanced error handling and metrics"""
    with LoggingContext(operation="user_deletion", user_id=str(user_id)):
        logger.info(f"Deleting user {user_id}")
        await delete_user(user_id, db)
        return {"message": "User deleted successfully"}

@router.get("/search/{search_term}", response_model=List[UserResponseSchema])
# @api_endpoint(
#     rate_limit="50/minute",
#     timeout=20.0,
#     metrics_name="user_search"
# )
@handle_errors("User search failed")
async def search_users_endpoint(search_term: str, db: Session = Depends(get_db)):
    """Search users with enhanced error handling and metrics"""
    with LoggingContext(operation="user_search", search_term=search_term):
        logger.info(f"Searching users with term: {search_term}")
        return await search_users(search_term, db)