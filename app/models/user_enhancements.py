# Enhanced User Models for User Service Enhancements
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, Date
from sqlalchemy.dialects.postgresql import JSONB, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared_architecture.db.base import Base
from enum import Enum
from datetime import datetime
from typing import Dict, List, Any, Optional

# Enhanced Enums
class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive" 
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    LOCKED = "locked"
    ARCHIVED = "archived"

class OnboardingStatus(str, Enum):
    EMAIL_VERIFICATION = "email_verification"
    PHONE_VERIFICATION = "phone_verification"
    KYC_PENDING = "kyc_pending"
    DOCUMENT_UPLOAD = "document_upload"
    COMPLIANCE_REVIEW = "compliance_review"
    COMPLETED = "completed"

class MFAType(str, Enum):
    TOTP = "totp"  # Time-based One-Time Password (Google Authenticator)
    SMS = "sms"    # SMS verification
    EMAIL = "email" # Email verification
    BACKUP_CODES = "backup_codes"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SubscriptionTier(str, Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

# Enhanced User Status and Lifecycle
class UserStatusHistory(Base):
    """Track user status changes over time"""
    __tablename__ = "user_status_history"
    __table_args__ = {'schema': 'tradingdb', 'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("tradingdb.users.id"), nullable=False)
    old_status = Column(String(50))
    new_status = Column(String(50), nullable=False)
    reason = Column(Text)
    changed_by = Column(Integer, ForeignKey("tradingdb.users.id"))
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    changed_by_user = relationship("User", foreign_keys=[changed_by])

class UserOnboarding(Base):
    """Track user onboarding progress"""
    __tablename__ = "user_onboarding"
    __table_args__ = {'schema': 'tradingdb', 'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("tradingdb.users.id"), nullable=False, unique=True)
    current_step = Column(String(50), default=OnboardingStatus.EMAIL_VERIFICATION.value)
    completed_steps = Column(JSONB, default=list)  # List of completed steps
    step_data = Column(JSONB, default=dict)  # Step-specific data
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))  # Onboarding expiration
    
    # Relationships
    user = relationship("User", back_populates="onboarding")

# Multi-Factor Authentication
class UserMFA(Base):
    """Multi-factor authentication settings"""
    __tablename__ = "user_mfa"
    __table_args__ = {'schema': 'tradingdb', 'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("tradingdb.users.id"), nullable=False)
    mfa_type = Column(String(20), nullable=False)  # MFAType
    is_enabled = Column(Boolean, default=False)
    is_primary = Column(Boolean, default=False)
    
    # Type-specific data
    secret_key = Column(Text)  # TOTP secret, encrypted
    phone_number = Column(String(20))  # SMS number
    email_address = Column(String(255))  # Email for verification
    backup_codes = Column(JSONB)  # Encrypted backup codes
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True))
    use_count = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="mfa_methods")

class UserSession(Base):
    """Enhanced session management"""
    __tablename__ = "user_sessions"
    __table_args__ = {'schema': 'tradingdb', 'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("tradingdb.users.id"), nullable=False)
    session_token = Column(String(255), nullable=False, unique=True, index=True)
    refresh_token = Column(String(255), unique=True, index=True)
    
    # Session metadata
    device_id = Column(String(255))
    device_name = Column(String(255))
    device_type = Column(String(50))  # mobile, desktop, tablet
    browser = Column(String(100))
    os = Column(String(100))
    ip_address = Column(INET)
    location = Column(JSONB)  # City, country, coordinates
    
    # Session lifecycle
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    logout_at = Column(DateTime(timezone=True))
    logout_reason = Column(String(100))  # user_logout, timeout, force_logout
    
    # Security flags
    is_trusted_device = Column(Boolean, default=False)
    risk_score = Column(DECIMAL(3, 2), default=0.0)  # 0.0 to 1.0
    suspicious_activity = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")

# User Activity Tracking
class UserActivity(Base):
    """Comprehensive user activity tracking"""
    __tablename__ = "user_activities"
    __table_args__ = {'schema': 'tradingdb', 'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("tradingdb.users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("tradingdb.user_sessions.id"))
    
    # Activity details
    activity_type = Column(String(50), nullable=False)  # login, logout, view, create, update, delete
    resource_type = Column(String(50))  # user, permission, trade, etc.
    resource_id = Column(String(100))
    action_details = Column(JSONB)  # Detailed action data
    
    # Request metadata
    endpoint = Column(String(255))
    http_method = Column(String(10))
    request_data = Column(JSONB)
    response_status = Column(Integer)
    response_time_ms = Column(Integer)
    
    # Context
    ip_address = Column(INET)
    user_agent = Column(Text)
    referer = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Security and compliance
    is_sensitive = Column(Boolean, default=False)
    compliance_flags = Column(JSONB)
    risk_indicators = Column(JSONB)
    
    # Relationships
    user = relationship("User", back_populates="activities")
    session = relationship("UserSession")

# User Preferences
class UserPreferences(Base):
    """User preferences and settings"""
    __tablename__ = "user_preferences"
    __table_args__ = {'schema': 'tradingdb', 'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("tradingdb.users.id"), nullable=False, unique=True)
    
    # UI Preferences
    theme = Column(String(20), default="light")  # light, dark, auto
    language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    date_format = Column(String(20), default="YYYY-MM-DD")
    currency = Column(String(5), default="USD")
    
    # Notification Preferences
    email_notifications = Column(JSONB, default=dict)  # {login: true, trades: false, etc.}
    sms_notifications = Column(JSONB, default=dict)
    push_notifications = Column(JSONB, default=dict)
    in_app_notifications = Column(JSONB, default=dict)
    
    # Trading Preferences
    default_trading_account = Column(Integer)
    risk_warnings = Column(Boolean, default=True)
    confirmation_prompts = Column(JSONB, default=dict)  # {large_trades: true, etc.}
    
    # Privacy Settings
    profile_visibility = Column(String(20), default="private")  # public, friends, private
    activity_visibility = Column(String(20), default="private")
    allow_social_features = Column(Boolean, default=False)
    
    # Advanced Settings
    api_access_enabled = Column(Boolean, default=False)
    advanced_features = Column(JSONB, default=dict)
    custom_settings = Column(JSONB, default=dict)
    
    # Metadata
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="preferences")

# Organizations and Multi-tenancy
class Organization(Base):
    """Multi-tenant organization management"""
    __tablename__ = "organizations"
    __table_args__ = {'schema': 'tradingdb', 'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    display_name = Column(String(255))
    description = Column(Text)
    
    # Organization details
    organization_type = Column(String(50))  # trading_firm, hedge_fund, bank, individual
    registration_number = Column(String(100))
    tax_id = Column(String(50))
    website = Column(String(255))
    
    # Subscription and billing
    subscription_tier = Column(String(50), default=SubscriptionTier.BASIC.value)
    billing_email = Column(String(255))
    subscription_starts = Column(Date)
    subscription_expires = Column(Date)
    
    # Configuration
    settings = Column(JSONB, default=dict)  # Org-specific configurations
    compliance_requirements = Column(JSONB, default=dict)
    risk_settings = Column(JSONB, default=dict)
    feature_flags = Column(JSONB, default=dict)
    
    # Address and contact
    address = Column(JSONB)  # Street, city, country, postal_code
    contact_info = Column(JSONB)  # Phone, fax, support_email
    
    # Status and lifecycle
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("tradingdb.users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    members = relationship("UserOrganizationRole", back_populates="organization")

class UserOrganizationRole(Base):
    """User roles within organizations"""
    __tablename__ = "user_organization_roles"
    __table_args__ = {'schema': 'tradingdb', 'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("tradingdb.users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("tradingdb.organizations.id"), nullable=False)
    
    # Role and permissions
    role = Column(String(50), nullable=False)  # admin, manager, trader, viewer, compliance
    department = Column(String(100))  # trading, compliance, risk, operations
    title = Column(String(100))  # Job title
    
    # Organization-specific permissions
    permissions = Column(JSONB, default=dict)
    restrictions = Column(JSONB, default=dict)
    
    # Role lifecycle
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    
    # Manager and reporting
    reports_to = Column(Integer, ForeignKey("tradingdb.user_organization_roles.id"))
    is_manager = Column(Boolean, default=False)
    
    # Metadata
    invited_by = Column(Integer, ForeignKey("tradingdb.users.id"))
    invited_at = Column(DateTime(timezone=True), server_default=func.now())
    joined_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="organization_roles")
    organization = relationship("Organization", back_populates="members")
    manager = relationship("UserOrganizationRole", remote_side=[id])
    invited_by_user = relationship("User", foreign_keys=[invited_by])

# Compliance and Risk Management
class ComplianceProfile(Base):
    """User compliance and KYC information"""
    __tablename__ = "compliance_profiles"
    __table_args__ = {'schema': 'tradingdb', 'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("tradingdb.users.id"), nullable=False, unique=True)
    
    # KYC Status
    kyc_status = Column(String(50), default="not_started")  # not_started, pending, approved, rejected
    kyc_level = Column(Integer, default=0)  # 0, 1, 2, 3 (increasing verification levels)
    kyc_completed_at = Column(DateTime(timezone=True))
    kyc_expires_at = Column(DateTime(timezone=True))
    
    # Risk Assessment
    risk_rating = Column(String(20), default=RiskLevel.LOW.value)
    risk_score = Column(DECIMAL(5, 2), default=0.0)  # 0.0 to 100.0
    risk_factors = Column(JSONB, default=list)
    last_risk_assessment = Column(DateTime(timezone=True))
    
    # Regulatory Information
    regulatory_flags = Column(JSONB, default=dict)
    sanctions_check_status = Column(String(50))
    sanctions_check_date = Column(DateTime(timezone=True))
    pep_status = Column(Boolean, default=False)  # Politically Exposed Person
    
    # Documentation
    documents_required = Column(JSONB, default=list)
    documents_submitted = Column(JSONB, default=list)
    documents_verified = Column(JSONB, default=list)
    
    # Compliance Reviews
    last_compliance_review = Column(DateTime(timezone=True))
    next_review_due = Column(DateTime(timezone=True))
    compliance_notes = Column(Text)
    reviewed_by = Column(Integer, ForeignKey("tradingdb.users.id"))
    
    # Trading Limits (compliance-driven)
    trading_limits = Column(JSONB, default=dict)
    enhanced_due_diligence = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="compliance_profile")
    reviewer = relationship("User", foreign_keys=[reviewed_by])

# User Analytics and Metrics
class UserMetrics(Base):
    """Daily user metrics and analytics"""
    __tablename__ = "user_metrics"
    __table_args__ = {'schema': 'tradingdb', 'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("tradingdb.users.id"), nullable=False)
    metric_date = Column(Date, nullable=False)
    
    # Activity Metrics
    login_count = Column(Integer, default=0)
    session_duration_seconds = Column(Integer, default=0)
    page_views = Column(Integer, default=0)
    api_calls = Column(Integer, default=0)
    
    # Feature Usage
    features_used = Column(JSONB, default=dict)  # {trading: 5, analytics: 2, etc.}
    actions_performed = Column(JSONB, default=dict)  # {create: 3, update: 5, etc.}
    
    # Performance Metrics
    avg_response_time_ms = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    error_types = Column(JSONB, default=dict)
    
    # Engagement Metrics
    unique_features_accessed = Column(Integer, default=0)
    help_requests = Column(Integer, default=0)
    feedback_submitted = Column(Integer, default=0)
    
    # Security Metrics
    failed_login_attempts = Column(Integer, default=0)
    mfa_challenges = Column(Integer, default=0)
    suspicious_activities = Column(Integer, default=0)
    
    # Metadata
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="metrics")

# Enhanced Audit Trail
class AuditTrail(Base):
    """Comprehensive audit trail for compliance"""
    __tablename__ = "audit_trail"
    __table_args__ = {'schema': 'tradingdb', 'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Who and When
    user_id = Column(Integer, ForeignKey("tradingdb.users.id"))
    session_id = Column(Integer, ForeignKey("tradingdb.user_sessions.id"))
    actor_type = Column(String(50), default="user")  # user, system, admin, api
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # What happened
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100))
    resource_name = Column(String(255))
    
    # Change details
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    change_summary = Column(Text)
    
    # Context
    organization_id = Column(Integer, ForeignKey("tradingdb.organizations.id"))
    department = Column(String(100))
    business_justification = Column(Text)
    compliance_notes = Column(Text)
    
    # Technical details
    ip_address = Column(INET)
    user_agent = Column(Text)
    api_endpoint = Column(String(255))
    request_id = Column(String(100))
    
    # Classification
    sensitivity_level = Column(String(20), default="normal")  # low, normal, high, critical
    compliance_relevant = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=False)
    
    # Approval workflow
    approved_by = Column(Integer, ForeignKey("tradingdb.users.id"))
    approved_at = Column(DateTime(timezone=True))
    approval_notes = Column(Text)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    session = relationship("UserSession")
    organization = relationship("Organization")
    approver = relationship("User", foreign_keys=[approved_by])

# Add relationships to existing User model
def enhance_user_model():
    """Add new relationships to the existing User model"""
    from app.models.user import User
    
    # Add new relationships
    User.onboarding = relationship("UserOnboarding", back_populates="user", uselist=False)
    User.mfa_methods = relationship("UserMFA", back_populates="user")
    User.sessions = relationship("UserSession", back_populates="user")
    User.activities = relationship("UserActivity", back_populates="user")
    User.preferences = relationship("UserPreferences", back_populates="user", uselist=False)
    User.organization_roles = relationship("UserOrganizationRole", foreign_keys="UserOrganizationRole.user_id", back_populates="user")
    User.compliance_profile = relationship("ComplianceProfile", back_populates="user", uselist=False)
    User.metrics = relationship("UserMetrics", back_populates="user")
    
    return User