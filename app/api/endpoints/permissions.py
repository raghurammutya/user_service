# Permissions and Restrictions API endpoints
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from app.core.dependencies import get_db
from app.models.permissions import (
    UserPermission, TradingRestriction, DataSharingTemplate, PermissionAuditLog,
    PermissionType, ResourceType, ActionType, PermissionLevel, ScopeType, EnforcementType,
    PermissionEvaluator, PermissionResult, create_share_all_except_permissions,
    create_instrument_trading_restrictions
)
from app.models.user import User
from shared_architecture.auth import get_current_user, UserContext
from shared_architecture.utils.enhanced_logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Pydantic schemas for API requests/responses
class DataSharingRequest(BaseModel):
    resource_types: List[str] = Field(..., description="Types of data to share (positions, holdings, etc.)")
    scope: str = Field(..., description="Sharing scope: 'all', 'specific', 'all_except'")
    allowed_users: Optional[List[int]] = Field(None, description="Specific users to allow (for 'specific' scope)")
    excluded_users: Optional[List[int]] = Field(None, description="Users to exclude (for 'all_except' scope)")
    expires_at: Optional[datetime] = Field(None, description="When permission expires")
    notes: Optional[str] = Field(None, description="Reason for sharing")

class TradingPermissionRequest(BaseModel):
    grantee_user_id: int = Field(..., description="User receiving permission")
    permissions: List[Dict[str, Any]] = Field(..., description="List of permission configurations")
    expires_at: Optional[datetime] = Field(None, description="When permissions expire")
    notes: Optional[str] = Field(None, description="Reason for granting permissions")

class TradingRestrictionRequest(BaseModel):
    target_user_id: int = Field(..., description="User to restrict")
    restrictions: List[Dict[str, Any]] = Field(..., description="List of restriction configurations")
    expires_at: Optional[datetime] = Field(None, description="When restrictions expire")
    notes: Optional[str] = Field(None, description="Reason for restrictions")

class PermissionCheckRequest(BaseModel):
    user_id: int = Field(..., description="User to check permissions for")
    action: str = Field(..., description="Action to check (view, create, modify, exit)")
    resource: str = Field(..., description="Resource type (positions, holdings, etc.)")
    instrument_key: Optional[str] = Field(None, description="Specific instrument (optional)")

class PermissionResponse(BaseModel):
    allowed: bool
    reason: str
    priority: int
    rule_details: Optional[Dict[str, Any]] = None

# Data Sharing APIs
@router.post("/data-sharing")
async def grant_data_sharing_permission(
    request: DataSharingRequest,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Grant data sharing permissions with flexible scope control"""
    
    try:
        permissions_created = []
        
        if request.scope == "all_except":
            # Share with all users except excluded ones
            excluded_users = request.excluded_users or []
            permissions = create_share_all_except_permissions(
                grantor_id=current_user.user_id,
                excluded_user_ids=excluded_users,
                resource_types=request.resource_types,
                db_session=db
            )
            
            for permission in permissions:
                permission.expires_at = request.expires_at
                permission.notes = request.notes
                db.add(permission)
                permissions_created.append(permission)
                
        elif request.scope == "specific":
            # Share with specific users only
            allowed_users = request.allowed_users or []
            
            for user_id in allowed_users:
                for resource_type in request.resource_types:
                    permission = UserPermission(
                        grantor_user_id=current_user.user_id,
                        grantee_user_id=user_id,
                        permission_type=PermissionType.DATA_SHARING,
                        resource_type=resource_type,
                        action_type=ActionType.VIEW,
                        permission_level=PermissionLevel.ALLOW,
                        scope_type=ScopeType.SPECIFIC,
                        granted_by=current_user.user_id,
                        expires_at=request.expires_at,
                        notes=request.notes
                    )
                    db.add(permission)
                    permissions_created.append(permission)
                    
        elif request.scope == "all":
            # Share with all users
            for resource_type in request.resource_types:
                permission = UserPermission(
                    grantor_user_id=current_user.user_id,
                    grantee_user_id=0,  # Special ID for "all users"
                    permission_type=PermissionType.DATA_SHARING,
                    resource_type=resource_type,
                    action_type=ActionType.VIEW,
                    permission_level=PermissionLevel.ALLOW,
                    scope_type=ScopeType.ALL,
                    granted_by=current_user.user_id,
                    expires_at=request.expires_at,
                    notes=request.notes
                )
                db.add(permission)
                permissions_created.append(permission)
        
        db.commit()
        
        # Log the action
        logger.info(f"User {current_user.user_id} granted data sharing permissions: {request.scope} scope for {request.resource_types}")
        
        return {
            "message": "Data sharing permissions granted successfully",
            "permissions_created": len(permissions_created),
            "scope": request.scope,
            "resource_types": request.resource_types
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to grant data sharing permissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grant permissions: {str(e)}"
        )

@router.get("/data-sharing/my-settings")
async def get_my_data_sharing_settings(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's data sharing settings"""
    
    permissions = db.query(UserPermission).filter(
        UserPermission.grantor_user_id == current_user.user_id,
        UserPermission.permission_type == PermissionType.DATA_SHARING,
        UserPermission.is_active == True
    ).all()
    
    settings = {}
    for permission in permissions:
        resource = permission.resource_type
        if resource not in settings:
            settings[resource] = {"allowed": [], "denied": []}
        
        if permission.permission_level == PermissionLevel.ALLOW:
            if permission.grantee_user_id == 0:
                settings[resource]["scope"] = "all"
            else:
                settings[resource]["allowed"].append(permission.grantee_user_id)
        else:
            settings[resource]["denied"].append(permission.grantee_user_id)
    
    return {"data_sharing_settings": settings}

@router.get("/data-sharing/viewers")
async def get_data_viewers(
    resource_type: str = Query(..., description="Resource type to check"),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of users who can view my data for a specific resource"""
    
    # Get allow permissions
    allow_permissions = db.query(UserPermission).filter(
        UserPermission.grantor_user_id == current_user.user_id,
        UserPermission.permission_type == PermissionType.DATA_SHARING,
        UserPermission.resource_type == resource_type,
        UserPermission.permission_level == PermissionLevel.ALLOW,
        UserPermission.is_active == True
    ).all()
    
    # Get deny permissions
    deny_permissions = db.query(UserPermission).filter(
        UserPermission.grantor_user_id == current_user.user_id,
        UserPermission.permission_type == PermissionType.DATA_SHARING,
        UserPermission.resource_type == resource_type,
        UserPermission.permission_level == PermissionLevel.DENY,
        UserPermission.is_active == True
    ).all()
    
    allowed_users = []
    denied_users = [p.grantee_user_id for p in deny_permissions]
    
    for permission in allow_permissions:
        if permission.grantee_user_id == 0:
            # All users allowed, but exclude denied ones
            all_users = db.query(User.id).filter(User.id != current_user.user_id).all()
            allowed_users = [u.id for u in all_users if u.id not in denied_users]
            break
        else:
            if permission.grantee_user_id not in denied_users:
                allowed_users.append(permission.grantee_user_id)
    
    return {
        "resource_type": resource_type,
        "viewers": allowed_users,
        "explicitly_denied": denied_users
    }

# Trading Permissions APIs
@router.post("/trading")
async def grant_trading_permissions(
    request: TradingPermissionRequest,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Grant trading permissions with instrument-level control"""
    
    try:
        permissions_created = []
        
        for perm_config in request.permissions:
            action = perm_config.get("action", "all")
            scope = perm_config.get("scope", "all")
            instruments = perm_config.get("instruments", [])
            
            # Create instrument filters based on scope
            instrument_filters = None
            if scope == "whitelist" and instruments:
                instrument_filters = {"whitelist": instruments}
            elif scope == "blacklist" and instruments:
                instrument_filters = {"blacklist": instruments}
            
            permission = UserPermission(
                grantor_user_id=current_user.user_id,
                grantee_user_id=request.grantee_user_id,
                permission_type=PermissionType.TRADING_ACTION,
                resource_type=ResourceType.POSITIONS,  # Default to positions
                action_type=action,
                permission_level=PermissionLevel.ALLOW,
                scope_type=ScopeType.SPECIFIC if instruments else ScopeType.ALL,
                instrument_filters=instrument_filters,
                granted_by=current_user.user_id,
                expires_at=request.expires_at,
                notes=request.notes
            )
            
            db.add(permission)
            permissions_created.append(permission)
        
        db.commit()
        
        logger.info(f"User {current_user.user_id} granted trading permissions to user {request.grantee_user_id}")
        
        return {
            "message": "Trading permissions granted successfully",
            "permissions_created": len(permissions_created),
            "grantee_user_id": request.grantee_user_id
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to grant trading permissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grant trading permissions: {str(e)}"
        )

@router.post("/trading/check")
async def check_trading_permission(
    request: PermissionCheckRequest,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PermissionResponse:
    """Check if a user has permission to perform a trading action"""
    
    try:
        # Use permission evaluator to check permission
        result = PermissionEvaluator.evaluate_permission(
            user_id=request.user_id,
            action=request.action,
            resource=request.resource,
            instrument_key=request.instrument_key,
            db_session=db
        )
        
        return PermissionResponse(
            allowed=result.allowed,
            reason=result.reason,
            priority=result.priority,
            rule_details=result.rule
        )
        
    except Exception as e:
        logger.error(f"Failed to check trading permission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check permission: {str(e)}"
        )

# Trading Restrictions APIs
@router.post("/restrictions/trading")
async def apply_trading_restrictions(
    request: TradingRestrictionRequest,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Apply trading restrictions to a user"""
    
    try:
        restrictions_created = []
        
        for restriction_config in request.restrictions:
            restriction_type = restriction_config.get("type", "instrument_blacklist")
            actions = restriction_config.get("actions", ["all"])
            instruments = restriction_config.get("instruments", [])
            enforcement = restriction_config.get("enforcement", "HARD")
            priority = restriction_config.get("priority", 5)
            
            for action in actions:
                restriction = TradingRestriction(
                    user_id=request.target_user_id,
                    restrictor_user_id=current_user.user_id,
                    restriction_type=restriction_type,
                    action_type=action,
                    instrument_keys=instruments,
                    priority_level=priority,
                    enforcement_type=enforcement,
                    expires_at=request.expires_at,
                    notes=request.notes
                )
                
                db.add(restriction)
                restrictions_created.append(restriction)
        
        db.commit()
        
        logger.info(f"User {current_user.user_id} applied trading restrictions to user {request.target_user_id}")
        
        return {
            "message": "Trading restrictions applied successfully",
            "restrictions_created": len(restrictions_created),
            "target_user_id": request.target_user_id
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to apply trading restrictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply restrictions: {str(e)}"
        )

@router.get("/restrictions/my-restrictions")
async def get_my_trading_restrictions(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trading restrictions applied to current user"""
    
    restrictions = db.query(TradingRestriction).filter(
        TradingRestriction.user_id == current_user.user_id,
        TradingRestriction.is_active == True
    ).all()
    
    restrictions_data = []
    for restriction in restrictions:
        restrictions_data.append({
            "id": restriction.id,
            "restriction_type": restriction.restriction_type,
            "action_type": restriction.action_type,
            "instrument_keys": restriction.instrument_keys,
            "enforcement_type": restriction.enforcement_type,
            "priority_level": restriction.priority_level,
            "applied_by": restriction.restrictor_user_id,
            "applied_at": restriction.applied_at,
            "expires_at": restriction.expires_at,
            "notes": restriction.notes
        })
    
    return {"restrictions": restrictions_data}

# Permission Templates APIs
@router.get("/templates")
async def get_permission_templates(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available permission templates"""
    
    templates = db.query(DataSharingTemplate).filter(
        DataSharingTemplate.owner_user_id == current_user.user_id,
        DataSharingTemplate.is_active == True
    ).all()
    
    template_data = []
    for template in templates:
        template_data.append({
            "id": template.id,
            "template_name": template.template_name,
            "description": template.description,
            "default_permissions": template.default_permissions,
            "restricted_users": template.restricted_users,
            "allowed_users": template.allowed_users
        })
    
    return {"templates": template_data}

# Utility endpoints
@router.delete("/revoke/{permission_id}")
async def revoke_permission(
    permission_id: int,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke a specific permission"""
    
    permission = db.query(UserPermission).filter(
        UserPermission.id == permission_id,
        UserPermission.grantor_user_id == current_user.user_id
    ).first()
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found or not authorized"
        )
    
    permission.is_active = False
    permission.revoked_at = datetime.utcnow()
    permission.revoked_by = current_user.user_id
    
    db.commit()
    
    logger.info(f"User {current_user.user_id} revoked permission {permission_id}")
    
    return {"message": "Permission revoked successfully"}

@router.get("/audit-log")
async def get_permission_audit_log(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get permission audit log for current user"""
    
    logs = db.query(PermissionAuditLog).filter(
        (PermissionAuditLog.actor_user_id == current_user.user_id) |
        (PermissionAuditLog.target_user_id == current_user.user_id)
    ).order_by(PermissionAuditLog.action_timestamp.desc()).offset(offset).limit(limit).all()
    
    audit_data = []
    for log in logs:
        audit_data.append({
            "id": log.id,
            "action_type": log.action_type,
            "actor_user_id": log.actor_user_id,
            "target_user_id": log.target_user_id,
            "table_name": log.table_name,
            "change_reason": log.change_reason,
            "action_timestamp": log.action_timestamp
        })
    
    return {"audit_log": audit_data, "total": len(audit_data)}