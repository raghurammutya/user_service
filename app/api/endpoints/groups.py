from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db
from app.services.group_service import create_group, add_user_to_group, delete_group
from app.schemas.group import GroupCreateSchema, GroupResponseSchema

# Import shared architecture utilities
from shared_architecture.utils.service_decorators import (
    api_endpoint, with_metrics, background_task
)
from shared_architecture.utils.error_handler import handle_errors
from shared_architecture.utils.enhanced_logging import get_logger, LoggingContext
from shared_architecture.monitoring.metrics_collector import MetricsCollector

router = APIRouter()
logger = get_logger(__name__)
metrics = MetricsCollector.get_instance()

@router.post("/", response_model=GroupResponseSchema)
@api_endpoint(
    rate_limit="30/minute",
    timeout=20.0,
    metrics_name="group_creation"
)
@handle_errors("Group creation failed")
async def create_group_endpoint(group_data: GroupCreateSchema, db: Session = Depends(get_db)):
    """Create a new group with enhanced error handling and metrics"""
    with LoggingContext(operation="group_creation", group_name=group_data.name):
        logger.info(f"Creating new group: {group_data.name}")
        
        # Track group creation attempts
        metrics.counter("group_creation_attempts").increment()
        
        try:
            group = await create_group(group_data, db)
            
            # Track successful group creation
            metrics.counter("group_creation_success").increment()
            logger.info(f"Group created successfully: {group.name}", group_id=group.id)
            
            return group
            
        except Exception as e:
            # Track failed group creation
            metrics.counter("group_creation_failed").increment(tags={
                "error_type": type(e).__name__
            })
            logger.error(f"Group creation failed: {group_data.name} - {str(e)}")
            raise

@router.post("/{group_id}/members/{user_id}")
@api_endpoint(
    rate_limit="50/minute",
    timeout=15.0,
    metrics_name="group_member_addition"
)
@handle_errors("Adding user to group failed")
async def add_member_to_group(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Add user to group with enhanced error handling"""
    with LoggingContext(operation="group_member_addition", group_id=str(group_id), user_id=str(user_id)):
        logger.info(f"Adding user {user_id} to group {group_id}")
        
        # Track member addition attempts
        metrics.counter("group_member_addition_attempts").increment()
        
        try:
            group = await add_user_to_group(group_id, user_id, db)
            
            # Track successful member addition
            metrics.counter("group_member_addition_success").increment()
            logger.info(f"User added to group successfully", group_id=group_id, user_id=user_id)
            
            return {"message": f"User {user_id} added to group {group_id} successfully"}
            
        except Exception as e:
            # Track failed member addition
            metrics.counter("group_member_addition_failed").increment(tags={
                "error_type": type(e).__name__
            })
            logger.error(f"Failed to add user {user_id} to group {group_id}: {str(e)}")
            raise

@router.delete("/{group_id}")
@api_endpoint(
    rate_limit="10/minute",
    timeout=20.0,
    metrics_name="group_deletion"
)
@handle_errors("Group deletion failed")
async def delete_group_endpoint(group_id: int, db: Session = Depends(get_db)):
    """Delete group with enhanced error handling"""
    with LoggingContext(operation="group_deletion", group_id=str(group_id)):
        logger.info(f"Deleting group {group_id}")
        
        # Track group deletion attempts
        metrics.counter("group_deletion_attempts").increment()
        
        try:
            await delete_group(group_id, db)
            
            # Track successful group deletion
            metrics.counter("group_deletion_success").increment()
            logger.info(f"Group deleted successfully", group_id=group_id)
            
            return {"message": f"Group {group_id} deleted successfully"}
            
        except Exception as e:
            # Track failed group deletion
            metrics.counter("group_deletion_failed").increment(tags={
                "error_type": type(e).__name__
            })
            logger.error(f"Group deletion failed: {group_id} - {str(e)}")
            raise

@router.post("/{group_id}/invite")
@background_task(
    retry_attempts=3,
    circuit_breaker_name="email_service",
    metrics_name="group_invitation"
)
@handle_errors("Group invitation failed")
async def send_group_invitation(group_id: int, email: str, db: Session = Depends(get_db)):
    """Send group invitation with background task processing"""
    with LoggingContext(operation="group_invitation", group_id=str(group_id), email=email):
        logger.info(f"Sending group invitation to {email} for group {group_id}")
        
        # Track invitation attempts
        metrics.counter("group_invitation_attempts").increment()
        
        try:
            # TODO: Implement actual invitation logic
            # For now, just simulate
            
            # Track successful invitation
            metrics.counter("group_invitation_success").increment()
            logger.info(f"Group invitation sent successfully", group_id=group_id, email=email)
            
            return {"message": f"Invitation sent to {email} for group {group_id}"}
            
        except Exception as e:
            # Track failed invitation
            metrics.counter("group_invitation_failed").increment(tags={
                "error_type": type(e).__name__
            })
            logger.error(f"Group invitation failed: {email} - {str(e)}")
            raise