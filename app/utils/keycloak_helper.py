# Enhanced Keycloak integration using shared_architecture
from shared_architecture.utils.keycloak_helper import (
    get_access_token, refresh_access_token, 
    get_keycloak_manager, KeycloakUserManager
)
from shared_architecture.auth import get_jwt_manager, UserContext
from shared_architecture.utils.enhanced_logging import get_logger
from shared_architecture.exceptions.trade_exceptions import AuthenticationException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.core.config import settings
from app.models.user import User

logger = get_logger(__name__)

def get_keycloak_token(username: str, password: str) -> str:
    """
    Authenticate with Keycloak and retrieve an access token using shared helper.
    """
    auth_url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token"
    
    # Use shared architecture function
    return get_access_token(
        auth_url=auth_url,
        client_id=settings.keycloak_client_id,
        client_secret=getattr(settings, 'keycloak_client_secret', ""),
        username=username,
        password=password
    )

def refresh_keycloak_token(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh Keycloak access token using shared helper.
    """
    refresh_url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token"
    
    return refresh_access_token(
        refresh_url=refresh_url,
        client_id=settings.keycloak_client_id,
        client_secret=getattr(settings, 'keycloak_client_secret', ""),
        refresh_token=refresh_token
    )

async def authenticate_with_keycloak(username: str, password: str, db: Session) -> Dict[str, Any]:
    """
    Comprehensive Keycloak authentication with user provisioning
    """
    try:
        # Step 1: Get access token from Keycloak
        logger.info(f"Authenticating user with Keycloak: {username}")
        access_token = get_keycloak_token(username, password)
        
        # Step 2: Validate token and extract user context
        jwt_manager = get_jwt_manager()
        claims = await jwt_manager.validate_token(access_token)
        user_context = jwt_manager.extract_user_context(claims)
        
        # Step 3: Provision/sync user in local database
        local_user = await provision_or_sync_user(user_context, db)
        
        # Step 4: Return comprehensive auth response
        auth_response = {
            "access_token": access_token,
            "token_type": "bearer",
            "provider": "keycloak",
            "user": {
                "id": local_user.id,
                "email": local_user.email,
                "first_name": local_user.first_name,
                "last_name": local_user.last_name,
                "role": local_user.role.value,
                "keycloak_roles": user_context.roles,
                "permissions": user_context.permissions
            }
        }
        
        logger.info(f"Keycloak authentication successful for: {username}")
        return auth_response
        
    except Exception as e:
        logger.error(f"Keycloak authentication failed for {username}: {str(e)}")
        raise AuthenticationException(
            message="Keycloak authentication failed",
            details={"username": username, "error": str(e)}
        )

async def provision_or_sync_user(user_context: UserContext, db: Session) -> User:
    """
    Provision or sync user from Keycloak to local database
    """
    try:
        # Check if user exists locally
        existing_user = db.query(User).filter(User.email == user_context.email).first()
        
        if existing_user:
            # Update existing user with Keycloak data
            updated = False
            
            if existing_user.first_name != user_context.first_name and user_context.first_name:
                existing_user.first_name = user_context.first_name
                updated = True
                
            if existing_user.last_name != user_context.last_name and user_context.last_name:
                existing_user.last_name = user_context.last_name
                updated = True
                
            # Update role if Keycloak role is higher
            if user_context.local_user_role and existing_user.role != user_context.local_user_role:
                # Only upgrade roles, not downgrade (for security)
                role_hierarchy = {"VIEWER": 1, "EDITOR": 2, "ADMIN": 3}
                current_level = role_hierarchy.get(existing_user.role.value, 0)
                new_level = role_hierarchy.get(user_context.local_user_role.value, 0)
                
                if new_level > current_level:
                    existing_user.role = user_context.local_user_role
                    updated = True
                    logger.info(f"Upgraded user role from {existing_user.role.value} to {user_context.local_user_role.value}")
            
            if updated:
                db.commit()
                db.refresh(existing_user)
                logger.info(f"Updated existing user from Keycloak: {user_context.email}")
            
            return existing_user
        else:
            # Create new user from Keycloak data
            new_user = User(
                first_name=user_context.first_name or "",
                last_name=user_context.last_name or "",
                email=user_context.email,
                phone_number="",  # Not available from Keycloak by default
                role=user_context.local_user_role or UserRole.VIEWER
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            logger.info(f"Provisioned new user from Keycloak: {user_context.email}")
            return new_user
            
    except Exception as e:
        logger.error(f"Failed to provision/sync user: {str(e)}")
        db.rollback()
        raise AuthenticationException(
            message="Failed to provision user from Keycloak",
            details={"email": user_context.email, "error": str(e)}
        )

async def sync_local_user_to_keycloak(user: User, password: Optional[str] = None) -> bool:
    """
    Sync local user to Keycloak (for users created locally first)
    """
    try:
        keycloak_manager = get_keycloak_manager()
        
        # Check if user already exists in Keycloak
        keycloak_user = await keycloak_manager.get_keycloak_user_by_email(user.email)
        
        if not keycloak_user:
            # Create user in Keycloak
            user_data = {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
            
            if password:
                user_data["password"] = password
                
            keycloak_user_id = await keycloak_manager.create_keycloak_user(user_data)
            
            # Assign role based on local user role
            role_mapping = {
                UserRole.ADMIN: "admin",
                UserRole.EDITOR: "editor", 
                UserRole.VIEWER: "viewer"
            }
            
            keycloak_role = role_mapping.get(user.role, "viewer")
            await keycloak_manager.assign_role_to_user(keycloak_user_id, keycloak_role)
            
            logger.info(f"Successfully synced local user to Keycloak: {user.email}")
            return True
        else:
            logger.info(f"User already exists in Keycloak: {user.email}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to sync user to Keycloak: {str(e)}")
        return False