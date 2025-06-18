# Enhanced User Service API Endpoints
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, date
import pyotp
import qrcode
import io
import base64
from passlib.context import CryptContext

from app.core.dependencies import get_db
from app.models.user_enhancements import (
    UserStatus, OnboardingStatus, MFAType, RiskLevel, SubscriptionTier,
    UserStatusHistory, UserOnboarding, UserMFA, UserSession, UserActivity,
    UserPreferences, Organization, UserOrganizationRole, ComplianceProfile,
    UserMetrics, AuditTrail
)
from app.models.user import User
from shared_architecture.auth import get_current_user, UserContext
from shared_architecture.utils.enhanced_logging import get_logger

router = APIRouter()
logger = get_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic Schemas for Enhanced Features

class UserStatusUpdate(BaseModel):
    new_status: UserStatus
    reason: Optional[str] = None

class MFASetupRequest(BaseModel):
    mfa_type: MFAType
    phone_number: Optional[str] = None
    email_address: Optional[str] = None

class MFAVerifyRequest(BaseModel):
    mfa_type: MFAType
    code: str

class UserPreferencesUpdate(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    email_notifications: Optional[Dict[str, bool]] = None
    sms_notifications: Optional[Dict[str, bool]] = None
    push_notifications: Optional[Dict[str, bool]] = None

class OrganizationCreate(BaseModel):
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    organization_type: Optional[str] = None
    subscription_tier: SubscriptionTier = SubscriptionTier.BASIC

class UserInviteRequest(BaseModel):
    email: str
    role: str
    department: Optional[str] = None
    organization_id: int

class ComplianceUpdate(BaseModel):
    kyc_status: Optional[str] = None
    risk_rating: Optional[RiskLevel] = None
    compliance_notes: Optional[str] = None

# User Status Management
@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    status_update: UserStatusUpdate,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user status with audit trail"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check permissions (admin or self)
    if current_user.user_id != user_id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    old_status = getattr(user, 'status', UserStatus.ACTIVE.value)
    
    # Record status change in history
    status_history = UserStatusHistory(
        user_id=user_id,
        old_status=old_status,
        new_status=status_update.new_status.value,
        reason=status_update.reason,
        changed_by=current_user.user_id
    )
    db.add(status_history)
    
    # Update user status (assuming we add status field to User model)
    # user.status = status_update.new_status.value
    
    # Create audit trail entry
    audit_entry = AuditTrail(
        user_id=current_user.user_id,
        action="UPDATE_USER_STATUS",
        resource_type="user",
        resource_id=str(user_id),
        old_values={"status": old_status},
        new_values={"status": status_update.new_status.value},
        change_summary=f"User status changed from {old_status} to {status_update.new_status.value}",
        business_justification=status_update.reason,
        compliance_relevant=True
    )
    db.add(audit_entry)
    
    db.commit()
    
    logger.info(f"User {user_id} status updated to {status_update.new_status.value} by {current_user.user_id}")
    
    return {"message": "User status updated successfully", "new_status": status_update.new_status.value}

# Multi-Factor Authentication
@router.post("/users/mfa/setup")
async def setup_mfa(
    mfa_request: MFASetupRequest,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Setup multi-factor authentication"""
    
    if mfa_request.mfa_type == MFAType.TOTP:
        # Generate TOTP secret
        secret = pyotp.random_base32()
        
        # Create provisioning URI for QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=current_user.email,
            issuer_name="StocksBlitz Trading Platform"
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        qr_code_data = base64.b64encode(buf.getvalue()).decode()
        
        # Store MFA method (not verified yet)
        mfa_method = UserMFA(
            user_id=current_user.user_id,
            mfa_type=MFAType.TOTP.value,
            secret_key=secret,  # In production, encrypt this
            is_enabled=False,
            is_verified=False
        )
        db.add(mfa_method)
        db.commit()
        
        return {
            "secret": secret,
            "qr_code": qr_code_data,
            "provisioning_uri": provisioning_uri,
            "message": "Scan QR code with authenticator app and verify to enable TOTP"
        }
    
    elif mfa_request.mfa_type == MFAType.SMS:
        if not mfa_request.phone_number:
            raise HTTPException(status_code=400, detail="Phone number required for SMS MFA")
        
        # Store SMS MFA method
        mfa_method = UserMFA(
            user_id=current_user.user_id,
            mfa_type=MFAType.SMS.value,
            phone_number=mfa_request.phone_number,
            is_enabled=False,
            is_verified=False
        )
        db.add(mfa_method)
        db.commit()
        
        # TODO: Send SMS verification code
        return {"message": "SMS MFA setup initiated. Verification code sent to phone."}
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported MFA type")

@router.post("/users/mfa/verify")
async def verify_mfa(
    verify_request: MFAVerifyRequest,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify and enable MFA method"""
    
    mfa_method = db.query(UserMFA).filter(
        UserMFA.user_id == current_user.user_id,
        UserMFA.mfa_type == verify_request.mfa_type.value,
        UserMFA.is_verified == False
    ).first()
    
    if not mfa_method:
        raise HTTPException(status_code=404, detail="MFA method not found or already verified")
    
    if verify_request.mfa_type == MFAType.TOTP:
        totp = pyotp.TOTP(mfa_method.secret_key)
        if not totp.verify(verify_request.code):
            raise HTTPException(status_code=400, detail="Invalid TOTP code")
    
    # Mark as verified and enabled
    mfa_method.is_verified = True
    mfa_method.is_enabled = True
    mfa_method.last_used = datetime.utcnow()
    
    # If this is the first MFA method, make it primary
    primary_exists = db.query(UserMFA).filter(
        UserMFA.user_id == current_user.user_id,
        UserMFA.is_primary == True
    ).first()
    
    if not primary_exists:
        mfa_method.is_primary = True
    
    db.commit()
    
    # Log security event
    activity = UserActivity(
        user_id=current_user.user_id,
        activity_type="MFA_ENABLED",
        action_details={"mfa_type": verify_request.mfa_type.value},
        is_sensitive=True
    )
    db.add(activity)
    db.commit()
    
    return {"message": f"{verify_request.mfa_type.value.upper()} MFA enabled successfully"}

@router.get("/users/mfa/methods")
async def get_mfa_methods(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's MFA methods"""
    
    methods = db.query(UserMFA).filter(
        UserMFA.user_id == current_user.user_id
    ).all()
    
    return {
        "mfa_methods": [
            {
                "id": method.id,
                "type": method.mfa_type,
                "is_enabled": method.is_enabled,
                "is_primary": method.is_primary,
                "created_at": method.created_at,
                "last_used": method.last_used
            }
            for method in methods
        ]
    }

# User Activity and Sessions
@router.get("/users/sessions")
async def get_user_sessions(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's active sessions"""
    
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.user_id,
        UserSession.is_active == True
    ).order_by(UserSession.last_activity.desc()).all()
    
    return {
        "sessions": [
            {
                "id": session.id,
                "device_name": session.device_name,
                "device_type": session.device_type,
                "browser": session.browser,
                "ip_address": str(session.ip_address),
                "location": session.location,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "is_current": session.session_token == getattr(current_user, 'session_token', None)
            }
            for session in sessions
        ]
    }

@router.delete("/users/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke a specific session"""
    
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == current_user.user_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.is_active = False
    session.logout_at = datetime.utcnow()
    session.logout_reason = "user_revoked"
    
    db.commit()
    
    return {"message": "Session revoked successfully"}

@router.get("/users/activity")
async def get_user_activity(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    activity_type: Optional[str] = Query(None),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user activity history"""
    
    query = db.query(UserActivity).filter(UserActivity.user_id == current_user.user_id)
    
    if activity_type:
        query = query.filter(UserActivity.activity_type == activity_type)
    
    activities = query.order_by(UserActivity.timestamp.desc()).offset(offset).limit(limit).all()
    
    return {
        "activities": [
            {
                "id": activity.id,
                "activity_type": activity.activity_type,
                "resource_type": activity.resource_type,
                "resource_id": activity.resource_id,
                "action_details": activity.action_details,
                "timestamp": activity.timestamp,
                "ip_address": str(activity.ip_address) if activity.ip_address else None
            }
            for activity in activities
        ]
    }

# User Preferences
@router.get("/users/preferences")
async def get_user_preferences(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user preferences"""
    
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.user_id
    ).first()
    
    if not preferences:
        # Create default preferences
        preferences = UserPreferences(user_id=current_user.user_id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    
    return {
        "theme": preferences.theme,
        "language": preferences.language,
        "timezone": preferences.timezone,
        "date_format": preferences.date_format,
        "currency": preferences.currency,
        "email_notifications": preferences.email_notifications,
        "sms_notifications": preferences.sms_notifications,
        "push_notifications": preferences.push_notifications,
        "profile_visibility": preferences.profile_visibility,
        "api_access_enabled": preferences.api_access_enabled
    }

@router.put("/users/preferences")
async def update_user_preferences(
    preferences_update: UserPreferencesUpdate,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user preferences"""
    
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == current_user.user_id
    ).first()
    
    if not preferences:
        preferences = UserPreferences(user_id=current_user.user_id)
        db.add(preferences)
    
    # Update provided fields
    update_data = preferences_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preferences, field, value)
    
    db.commit()
    
    return {"message": "Preferences updated successfully"}

# Organization Management
@router.post("/organizations")
async def create_organization(
    org_create: OrganizationCreate,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new organization"""
    
    organization = Organization(
        name=org_create.name,
        display_name=org_create.display_name,
        description=org_create.description,
        organization_type=org_create.organization_type,
        subscription_tier=org_create.subscription_tier.value,
        created_by=current_user.user_id
    )
    
    db.add(organization)
    db.flush()  # Get the ID
    
    # Add creator as admin
    admin_role = UserOrganizationRole(
        user_id=current_user.user_id,
        organization_id=organization.id,
        role="admin",
        is_manager=True,
        invited_by=current_user.user_id,
        joined_at=datetime.utcnow()
    )
    
    db.add(admin_role)
    db.commit()
    
    return {
        "id": organization.id,
        "name": organization.name,
        "message": "Organization created successfully"
    }

@router.get("/organizations")
async def get_user_organizations(
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get organizations user belongs to"""
    
    roles = db.query(UserOrganizationRole).filter(
        UserOrganizationRole.user_id == current_user.user_id,
        UserOrganizationRole.is_active == True
    ).all()
    
    organizations = []
    for role in roles:
        org = role.organization
        organizations.append({
            "id": org.id,
            "name": org.name,
            "display_name": org.display_name,
            "subscription_tier": org.subscription_tier,
            "role": role.role,
            "department": role.department,
            "is_manager": role.is_manager
        })
    
    return {"organizations": organizations}

# Compliance Management
@router.get("/users/{user_id}/compliance")
async def get_compliance_profile(
    user_id: int,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user compliance profile"""
    
    # Check permissions
    if current_user.user_id != user_id and current_user.role not in ["ADMIN", "COMPLIANCE"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    profile = db.query(ComplianceProfile).filter(
        ComplianceProfile.user_id == user_id
    ).first()
    
    if not profile:
        # Create default compliance profile
        profile = ComplianceProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    return {
        "kyc_status": profile.kyc_status,
        "kyc_level": profile.kyc_level,
        "risk_rating": profile.risk_rating,
        "risk_score": float(profile.risk_score) if profile.risk_score else 0.0,
        "last_compliance_review": profile.last_compliance_review,
        "next_review_due": profile.next_review_due,
        "trading_limits": profile.trading_limits
    }

# User Metrics and Analytics
@router.get("/users/metrics")
async def get_user_metrics(
    days: int = Query(30, le=90),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user metrics for specified period"""
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    metrics = db.query(UserMetrics).filter(
        UserMetrics.user_id == current_user.user_id,
        UserMetrics.metric_date >= start_date,
        UserMetrics.metric_date <= end_date
    ).order_by(UserMetrics.metric_date.desc()).all()
    
    return {
        "metrics": [
            {
                "date": metric.metric_date,
                "login_count": metric.login_count,
                "session_duration_seconds": metric.session_duration_seconds,
                "page_views": metric.page_views,
                "api_calls": metric.api_calls,
                "features_used": metric.features_used,
                "error_count": metric.error_count
            }
            for metric in metrics
        ]
    }

# Audit Trail
@router.get("/audit-trail")
async def get_audit_trail(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    resource_type: Optional[str] = Query(None),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit trail for current user"""
    
    query = db.query(AuditTrail).filter(AuditTrail.user_id == current_user.user_id)
    
    if resource_type:
        query = query.filter(AuditTrail.resource_type == resource_type)
    
    entries = query.order_by(AuditTrail.timestamp.desc()).offset(offset).limit(limit).all()
    
    return {
        "audit_entries": [
            {
                "id": entry.id,
                "action": entry.action,
                "resource_type": entry.resource_type,
                "resource_id": entry.resource_id,
                "timestamp": entry.timestamp,
                "change_summary": entry.change_summary,
                "ip_address": str(entry.ip_address) if entry.ip_address else None
            }
            for entry in entries
        ]
    }