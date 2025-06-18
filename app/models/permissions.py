# User Permissions and Restrictions Models
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, DECIMAL, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared_architecture.db.base import Base
from typing import Dict, List, Any, Optional
from enum import Enum

class PermissionType(str, Enum):
    DATA_SHARING = "data_sharing"
    TRADING_ACTION = "trading_action"

class ResourceType(str, Enum):
    POSITIONS = "positions"
    HOLDINGS = "holdings"
    ORDERS = "orders"
    STRATEGIES = "strategies"
    MARGINS = "margins"

class ActionType(str, Enum):
    VIEW = "view"
    CREATE = "create"
    MODIFY = "modify"
    EXIT = "exit"
    ALL = "all"

class PermissionLevel(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"

class ScopeType(str, Enum):
    ALL = "ALL"
    SPECIFIC = "SPECIFIC"
    EXCLUDE = "EXCLUDE"

class EnforcementType(str, Enum):
    HARD = "HARD"    # Block action completely
    SOFT = "SOFT"    # Allow with warning
    WARNING = "WARNING"  # Log warning only

class UserPermission(Base):
    """Core permissions table for data sharing and trading actions"""
    __tablename__ = "user_permissions"
    __table_args__ = {'schema': 'tradingdb', 'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    grantor_user_id = Column(Integer, ForeignKey("tradingdb.users.id"), nullable=False)
    grantee_user_id = Column(Integer, ForeignKey("tradingdb.users.id"), nullable=False)
    permission_type = Column(String(50), nullable=False)  # PermissionType
    resource_type = Column(String(50), nullable=False)    # ResourceType
    action_type = Column(String(50))                      # ActionType
    permission_level = Column(String(20), default=PermissionLevel.ALLOW.value)
    scope_type = Column(String(20), default=ScopeType.ALL.value)
    
    # JSON fields for flexible configuration
    instrument_filters = Column(JSONB)                    # {"whitelist": [...], "blacklist": [...]}
    additional_conditions = Column(JSONB)                 # Time, value, frequency limits
    
    # Metadata
    granted_by = Column(Integer, ForeignKey("tradingdb.users.id"), nullable=False)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    revoked_at = Column(DateTime(timezone=True))
    revoked_by = Column(Integer, ForeignKey("tradingdb.users.id"))
    notes = Column(Text)
    
    # Relationships
    grantor = relationship("User", foreign_keys=[grantor_user_id], back_populates="granted_permissions")
    grantee = relationship("User", foreign_keys=[grantee_user_id], back_populates="received_permissions")
    granted_by_user = relationship("User", foreign_keys=[granted_by])
    revoked_by_user = relationship("User", foreign_keys=[revoked_by])

class DataSharingTemplate(Base):
    """Predefined templates for data sharing configurations"""
    __tablename__ = "data_sharing_templates"
    __table_args__ = {'schema': 'tradingdb', 'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String(100), nullable=False)
    description = Column(Text)
    owner_user_id = Column(Integer, ForeignKey("tradingdb.users.id"), nullable=False)
    
    # Template configuration
    default_permissions = Column(JSONB, nullable=False)   # Default sharing rules
    restricted_users = Column(JSONB)                      # Users explicitly denied
    allowed_users = Column(JSONB)                         # Users explicitly allowed
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    owner = relationship("User", back_populates="data_sharing_templates")

class TradingRestriction(Base):
    """Advanced trading restrictions and controls"""
    __tablename__ = "trading_restrictions"
    __table_args__ = {'schema': 'tradingdb', 'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("tradingdb.users.id"), nullable=False)
    restrictor_user_id = Column(Integer, ForeignKey("tradingdb.users.id"), nullable=False)
    restriction_type = Column(String(50), nullable=False)  # instrument_blacklist, action_limit, value_limit
    action_type = Column(String(50), nullable=False)       # ActionType
    
    # Restriction details
    instrument_keys = Column(JSONB)                        # Specific instruments affected
    value_limits = Column(JSONB)                           # Max position size, trade value, etc.
    time_restrictions = Column(JSONB)                      # Trading hours, days of week
    
    # Priority and enforcement
    priority_level = Column(Integer, default=1)           # Higher number = higher priority
    enforcement_type = Column(String(20), default=EnforcementType.HARD.value)
    
    # Metadata
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    notes = Column(Text)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="trading_restrictions")
    restrictor = relationship("User", foreign_keys=[restrictor_user_id])

class PermissionAuditLog(Base):
    """Audit log for all permission changes"""
    __tablename__ = "permission_audit_log"
    __table_args__ = {'schema': 'tradingdb', 'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String(50), nullable=False)      # GRANT, DENY, REVOKE, MODIFY
    permission_id = Column(Integer)                        # Reference to affected permission
    table_name = Column(String(50), nullable=False)       # Which table was affected
    
    # Who did what
    actor_user_id = Column(Integer, ForeignKey("tradingdb.users.id"), nullable=False)
    target_user_id = Column(Integer, ForeignKey("tradingdb.users.id"), nullable=False)
    
    # What changed
    old_values = Column(JSONB)                            # Previous state
    new_values = Column(JSONB)                            # New state
    change_reason = Column(Text)                          # Why the change was made
    
    # When and where
    action_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(INET)
    user_agent = Column(Text)
    
    # Relationships
    actor = relationship("User", foreign_keys=[actor_user_id])
    target = relationship("User", foreign_keys=[target_user_id])

class PermissionCache(Base):
    """Cache for permission evaluation results (performance optimization)"""
    __tablename__ = "permission_cache"
    __table_args__ = {'schema': 'tradingdb', 'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(255), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("tradingdb.users.id"), nullable=False)
    resource_type = Column(String(50), nullable=False)
    action_type = Column(String(50), nullable=False)
    instrument_key = Column(String(100))
    
    # Cached result
    permission_allowed = Column(Boolean, nullable=False)
    permission_reason = Column(String(100), nullable=False)
    priority_level = Column(Integer, default=1)
    
    # Cache metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())
    access_count = Column(Integer, default=1)
    
    # Relationships
    user = relationship("User", back_populates="permission_cache")

# Add back-references to User model
def add_permission_relationships():
    """Add permission relationships to User model"""
    from app.models.user import User
    
    # Add relationships for permissions
    User.granted_permissions = relationship("UserPermission", foreign_keys="UserPermission.grantor_user_id", back_populates="grantor")
    User.received_permissions = relationship("UserPermission", foreign_keys="UserPermission.grantee_user_id", back_populates="grantee")
    User.data_sharing_templates = relationship("DataSharingTemplate", back_populates="owner")
    User.trading_restrictions = relationship("TradingRestriction", foreign_keys="TradingRestriction.user_id", back_populates="user")
    User.permission_cache = relationship("PermissionCache", back_populates="user")

# Permission evaluation utilities
class PermissionResult:
    """Result of permission evaluation"""
    def __init__(self, allowed: bool, reason: str, rule: Optional[Dict] = None, priority: int = 1):
        self.allowed = allowed
        self.reason = reason
        self.rule = rule
        self.priority = priority
        
    def __str__(self):
        return f"PermissionResult(allowed={self.allowed}, reason='{self.reason}', priority={self.priority})"

class PermissionEvaluator:
    """Core permission evaluation engine"""
    
    @staticmethod
    def evaluate_permission(
        user_id: int,
        action: str,
        resource: str,
        instrument_key: Optional[str] = None,
        db_session = None
    ) -> PermissionResult:
        """
        Evaluate permission using hierarchy:
        1. EXPLICIT_DENY (highest priority)
        2. EXPLICIT_GRANT
        3. ROLE_BASED_DEFAULT
        4. SYSTEM_DEFAULT (lowest priority)
        """
        
        # 1. Check explicit denials (highest priority)
        denials = PermissionEvaluator._get_explicit_permissions(
            user_id, action, resource, instrument_key, PermissionLevel.DENY, db_session
        )
        if denials:
            return PermissionResult(
                allowed=False, 
                reason="EXPLICIT_DENY", 
                rule=denials[0],
                priority=denials[0].get('priority_level', 10)
            )
        
        # 2. Check explicit grants
        grants = PermissionEvaluator._get_explicit_permissions(
            user_id, action, resource, instrument_key, PermissionLevel.ALLOW, db_session
        )
        if grants:
            return PermissionResult(
                allowed=True, 
                reason="EXPLICIT_GRANT", 
                rule=grants[0],
                priority=grants[0].get('priority_level', 5)
            )
        
        # 3. Check role-based permissions
        role_permission = PermissionEvaluator._get_role_based_permission(user_id, action, resource, db_session)
        if role_permission:
            return PermissionResult(
                allowed=role_permission.allowed, 
                reason="ROLE_BASED",
                priority=3
            )
        
        # 4. System default (most restrictive)
        return PermissionResult(allowed=False, reason="SYSTEM_DEFAULT", priority=1)
    
    @staticmethod
    def _get_explicit_permissions(user_id, action, resource, instrument_key, permission_level, db_session):
        """Get explicit permissions from database"""
        # This would query the UserPermission table
        # Implementation depends on SQLAlchemy session
        return []
    
    @staticmethod  
    def _get_role_based_permission(user_id, action, resource, db_session):
        """Get role-based default permissions"""
        # This would check user role and apply default permissions
        return None

# Utility functions for common permission patterns
def create_share_all_except_permissions(grantor_id: int, excluded_user_ids: List[int], resource_types: List[str], db_session):
    """Create 'share with all except X' permissions"""
    permissions = []
    
    for resource_type in resource_types:
        # Create allow-all permission
        allow_all = UserPermission(
            grantor_user_id=grantor_id,
            grantee_user_id=0,  # Special ID for "all users"
            permission_type=PermissionType.DATA_SHARING,
            resource_type=resource_type,
            action_type=ActionType.VIEW,
            permission_level=PermissionLevel.ALLOW,
            scope_type=ScopeType.ALL,
            granted_by=grantor_id,
            notes=f"Share {resource_type} with all users"
        )
        permissions.append(allow_all)
        
        # Create explicit denials for excluded users
        for excluded_id in excluded_user_ids:
            deny_specific = UserPermission(
                grantor_user_id=grantor_id,
                grantee_user_id=excluded_id,
                permission_type=PermissionType.DATA_SHARING,
                resource_type=resource_type,
                action_type=ActionType.VIEW,
                permission_level=PermissionLevel.DENY,
                scope_type=ScopeType.SPECIFIC,
                granted_by=grantor_id,
                notes=f"Explicitly deny {resource_type} access to user {excluded_id}"
            )
            permissions.append(deny_specific)
    
    return permissions

def create_instrument_trading_restrictions(
    user_id: int, 
    restrictor_id: int, 
    blocked_instruments: List[str], 
    allowed_actions: List[str],
    db_session
) -> List[TradingRestriction]:
    """Create instrument-specific trading restrictions"""
    restrictions = []
    
    for action in allowed_actions:
        restriction = TradingRestriction(
            user_id=user_id,
            restrictor_user_id=restrictor_id,
            restriction_type="instrument_blacklist",
            action_type=action,
            instrument_keys=blocked_instruments,
            priority_level=10,
            enforcement_type=EnforcementType.HARD,
            notes=f"Block {action} actions for specified instruments"
        )
        restrictions.append(restriction)
    
    return restrictions