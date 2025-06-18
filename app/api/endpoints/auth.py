from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.dependencies import get_db
from app.services.auth_service import authenticate_user, login_user
from app.utils.keycloak_helper import get_keycloak_token, authenticate_with_keycloak

# Import shared architecture auth utilities
from shared_architecture.auth import get_current_user, UserContext
from app.models.user import User

# Import shared architecture utilities
from shared_architecture.utils.service_decorators import (
    api_endpoint, with_metrics, with_circuit_breaker
)
from shared_architecture.utils.error_handler import handle_errors
from shared_architecture.utils.enhanced_logging import get_logger, LoggingContext
from shared_architecture.monitoring.metrics_collector import MetricsCollector

router = APIRouter()
logger = get_logger(__name__)
metrics = MetricsCollector.get_instance()

@router.post("/login")
@api_endpoint(
    rate_limit="20/minute",
    timeout=15.0,
    metrics_name="user_login",
    circuit_breaker_name="auth_service"
)
@handle_errors("User login failed")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and return access token"""
    with LoggingContext(operation="user_login", username=form_data.username):
        logger.info(f"Login attempt for user: {form_data.username}")
        
        # Track login attempts
        metrics.counter("user_login_attempts").increment(tags={"username": form_data.username})
        
        try:
            # Authenticate user
            user = authenticate_user(form_data.username, form_data.password, db)
            
            # Generate token
            token_data = login_user(form_data.username, form_data.password, db)
            
            # Track successful login
            metrics.counter("user_login_success").increment(tags={"username": form_data.username})
            logger.info(f"User login successful: {form_data.username}")
            
            return token_data
            
        except Exception as e:
            # Track failed login
            metrics.counter("user_login_failed").increment(tags={
                "username": form_data.username,
                "error_type": type(e).__name__
            })
            logger.warning(f"User login failed: {form_data.username} - {str(e)}")
            raise

@router.post("/keycloak-login")
@api_endpoint(
    rate_limit="20/minute",
    timeout=20.0,
    metrics_name="keycloak_login",
    circuit_breaker_name="keycloak_service"
)
@handle_errors("Keycloak login failed")
async def keycloak_login(username: str, password: str, db: Session = Depends(get_db)):
    """Enhanced Keycloak authentication with user provisioning"""
    with LoggingContext(operation="keycloak_login", username=username):
        logger.info(f"Enhanced Keycloak login attempt for user: {username}")
        
        # Track Keycloak login attempts
        metrics.counter("keycloak_login_attempts").increment(tags={"username": username})
        
        try:
            # Use enhanced Keycloak authentication with user provisioning
            auth_response = await authenticate_with_keycloak(username, password, db)
            
            # Track successful Keycloak login
            metrics.counter("keycloak_login_success").increment(tags={
                "username": username,
                "user_id": str(auth_response["user"]["id"])
            })
            logger.info(f"Enhanced Keycloak login successful: {username}")
            
            return auth_response
            
        except Exception as e:
            # Track failed Keycloak login
            metrics.counter("keycloak_login_failed").increment(tags={
                "username": username,
                "error_type": type(e).__name__
            })
            logger.warning(f"Enhanced Keycloak login failed: {username} - {str(e)}")
            raise

@router.post("/logout")
@api_endpoint(
    rate_limit="50/minute",
    timeout=10.0,
    metrics_name="user_logout"
)
@handle_errors("User logout failed")
async def logout(token: str = None):
    """Logout user and invalidate token"""
    with LoggingContext(operation="user_logout"):
        logger.info("User logout request")
        
        # Track logout attempts
        metrics.counter("user_logout_attempts").increment()
        
        # TODO: Implement token invalidation logic
        # For now, just return success
        
        # Track successful logout
        metrics.counter("user_logout_success").increment()
        logger.info("User logout successful")
        
        return {"message": "Successfully logged out"}

@router.get("/me")
@api_endpoint(
    rate_limit="100/minute",
    timeout=10.0,
    metrics_name="get_current_user"
)
@handle_errors("Get current user failed")
async def get_current_user_info(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current authenticated user information from JWT token"""
    with LoggingContext(operation="get_current_user", user_id=current_user.user_id):
        logger.info(f"Get current user request for: {current_user.username}")
        
        # Track user info requests
        metrics.counter("user_info_requests").increment(tags={
            "user_id": current_user.user_id,
            "username": current_user.username
        })
        
        try:
            # Get local user data
            local_user = db.query(User).filter(User.email == current_user.email).first()
            
            if not local_user:
                # User exists in Keycloak but not locally - provision them
                from app.utils.keycloak_helper import provision_or_sync_user
                local_user = await provision_or_sync_user(current_user, db)
            
            # Return comprehensive user information
            user_info = {
                "id": local_user.id,
                "email": local_user.email,
                "username": current_user.username,
                "first_name": local_user.first_name,
                "last_name": local_user.last_name,
                "phone_number": local_user.phone_number,
                "role": local_user.role.value,
                "keycloak_user_id": current_user.user_id,
                "keycloak_roles": current_user.roles,
                "permissions": current_user.permissions,
                "groups": current_user.groups
            }
            
            logger.info(f"Successfully retrieved user info for: {current_user.username}")
            return user_info
            
        except Exception as e:
            logger.error(f"Failed to get user info: {str(e)}")
            metrics.counter("user_info_errors").increment(tags={
                "user_id": current_user.user_id,
                "error_type": type(e).__name__
            })
            raise