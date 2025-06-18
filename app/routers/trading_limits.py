# user_service/app/routers/trading_limits.py

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from shared_architecture.auth import get_current_user, UserContext
from app.core.dependencies import get_db
from shared_architecture.db.models.user_trading_limits import UserTradingLimit, TradingLimitType
from shared_architecture.db.models.trading_limit_breach import TradingLimitBreach
from shared_architecture.db.models.trading_account import TradingAccount
from shared_architecture.db.models.organization import Organization
from shared_architecture.schemas.trading_limits import (
    TradingLimitCreateSchema,
    TradingLimitUpdateSchema,
    TradingLimitResponseSchema,
    TradingLimitListSchema,
    TradingLimitUsageResetSchema,
    TradingLimitBreachResponseSchema,
    TradingLimitValidationSchema,
    TradingLimitValidationResultSchema,
    BulkTradingLimitCreateSchema,
    TradingLimitReportSchema
)
from shared_architecture.utils.trading_limit_validator import (
    TradingAction, 
    get_trading_limit_validator
)
# Temporarily disabled due to import issue in shared_architecture
# from shared_architecture.decorators.service_decorators import (
#     handle_service_errors,
#     log_service_call,
#     validate_permissions,
#     track_performance
# )
from shared_architecture.utils.enhanced_logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/trading-limits", tags=["Trading Limits"])

@router.post("", response_model=TradingLimitResponseSchema)
# @handle_service_errors
# @log_service_call
# @track_performance
async def create_trading_limit(
    schema: TradingLimitCreateSchema,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new trading limit for a user"""
    
    # Verify the user has permission to set limits for the target user
    if current_user.user_id != str(schema.user_id):
        # Check if current user is organization owner/admin
        trading_account = db.query(TradingAccount).filter(
            TradingAccount.id == schema.trading_account_id
        ).first()
        
        if not trading_account:
            raise HTTPException(status_code=404, detail="Trading account not found")
        
        organization = db.query(Organization).filter(
            Organization.id == trading_account.organization_id
        ).first()
        
        if not organization or organization.owner_id != int(current_user.user_id):
            raise HTTPException(
                status_code=403, 
                detail="Only organization owners can set limits for other users"
            )
    
    # Create the trading limit
    limit = UserTradingLimit(
        user_id=schema.user_id,
        trading_account_id=schema.trading_account_id,
        organization_id=trading_account.organization_id,
        strategy_id=schema.strategy_id,
        limit_type=schema.limit_type,
        limit_scope=schema.limit_scope,
        enforcement_type=schema.enforcement_type,
        limit_value=schema.limit_value,
        limit_percentage=schema.limit_percentage,
        limit_count=schema.limit_count,
        limit_text=schema.limit_text,
        start_time=schema.start_time,
        end_time=schema.end_time,
        allowed_days=schema.allowed_days,
        usage_reset_frequency=schema.usage_reset_frequency,
        override_allowed=schema.override_allowed,
        warning_threshold=schema.warning_threshold,
        notify_on_breach=schema.notify_on_breach,
        set_by_id=int(current_user.user_id)
    )
    
    db.add(limit)
    db.commit()
    db.refresh(limit)
    
    logger.info(f"Created trading limit {limit.id} for user {schema.user_id}")
    return TradingLimitResponseSchema.from_orm(limit)

@router.get("", response_model=TradingLimitListSchema)
# @handle_service_errors
# @log_service_call
async def list_trading_limits(
    user_id: Optional[int] = Query(None),
    trading_account_id: Optional[int] = Query(None),
    limit_type: Optional[TradingLimitType] = Query(None),
    is_active: Optional[bool] = Query(True),
    is_breached: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List trading limits with filtering"""
    
    query = db.query(UserTradingLimit)
    
    # Apply filters
    if user_id:
        query = query.filter(UserTradingLimit.user_id == user_id)
    if trading_account_id:
        query = query.filter(UserTradingLimit.trading_account_id == trading_account_id)
    if limit_type:
        query = query.filter(UserTradingLimit.limit_type == limit_type)
    if is_active is not None:
        query = query.filter(UserTradingLimit.is_active == is_active)
    
    # Filter by organization access
    query = query.join(TradingAccount).join(Organization).filter(
        Organization.owner_id == int(current_user.user_id)
    )
    
    total = query.count()
    limits = query.offset(skip).limit(limit).all()
    
    # Calculate summary statistics
    active_count = sum(1 for l in limits if l.is_active)
    breached_count = sum(1 for l in limits if l.is_breached)
    warning_count = sum(1 for l in limits if l.should_warn)
    
    return TradingLimitListSchema(
        limits=[TradingLimitResponseSchema.from_orm(l) for l in limits],
        total=total,
        active_count=active_count,
        breached_count=breached_count,
        warning_count=warning_count
    )

@router.get("/{limit_id}", response_model=TradingLimitResponseSchema)
# @handle_service_errors
# @log_service_call
async def get_trading_limit(
    limit_id: int = Path(...),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific trading limit"""
    
    limit = db.query(UserTradingLimit).filter(UserTradingLimit.id == limit_id).first()
    if not limit:
        raise HTTPException(status_code=404, detail="Trading limit not found")
    
    # Check access permissions
    trading_account = db.query(TradingAccount).filter(
        TradingAccount.id == limit.trading_account_id
    ).first()
    organization = db.query(Organization).filter(
        Organization.id == trading_account.organization_id
    ).first()
    
    if (limit.user_id != int(current_user.user_id) and 
        organization.owner_id != int(current_user.user_id)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return TradingLimitResponseSchema.from_orm(limit)

@router.put("/{limit_id}", response_model=TradingLimitResponseSchema)
# @handle_service_errors
# @log_service_call
# @track_performance
async def update_trading_limit(
    limit_id: int = Path(...),
    schema: TradingLimitUpdateSchema = ...,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a trading limit"""
    
    limit = db.query(UserTradingLimit).filter(UserTradingLimit.id == limit_id).first()
    if not limit:
        raise HTTPException(status_code=404, detail="Trading limit not found")
    
    # Check permissions (only organization owner can update)
    trading_account = db.query(TradingAccount).filter(
        TradingAccount.id == limit.trading_account_id
    ).first()
    organization = db.query(Organization).filter(
        Organization.id == trading_account.organization_id
    ).first()
    
    if organization.owner_id != int(current_user.user_id):
        raise HTTPException(status_code=403, detail="Only organization owners can update limits")
    
    # Update fields
    update_data = schema.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(limit, field, value)
    
    db.commit()
    db.refresh(limit)
    
    logger.info(f"Updated trading limit {limit_id}")
    return TradingLimitResponseSchema.from_orm(limit)

@router.delete("/{limit_id}")
# @handle_service_errors
# @log_service_call
async def delete_trading_limit(
    limit_id: int = Path(...),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a trading limit"""
    
    limit = db.query(UserTradingLimit).filter(UserTradingLimit.id == limit_id).first()
    if not limit:
        raise HTTPException(status_code=404, detail="Trading limit not found")
    
    # Check permissions
    trading_account = db.query(TradingAccount).filter(
        TradingAccount.id == limit.trading_account_id
    ).first()
    organization = db.query(Organization).filter(
        Organization.id == trading_account.organization_id
    ).first()
    
    if organization.owner_id != int(current_user.user_id):
        raise HTTPException(status_code=403, detail="Only organization owners can delete limits")
    
    db.delete(limit)
    db.commit()
    
    logger.info(f"Deleted trading limit {limit_id}")
    return {"message": "Trading limit deleted successfully"}

@router.post("/validate", response_model=TradingLimitValidationResultSchema)
# @handle_service_errors
# @log_service_call
# @track_performance
async def validate_trading_action(
    schema: TradingLimitValidationSchema,
    trading_account_id: int = Query(...),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate a trading action against all applicable limits"""
    
    trading_account = db.query(TradingAccount).filter(
        TradingAccount.id == trading_account_id
    ).first()
    
    if not trading_account:
        raise HTTPException(status_code=404, detail="Trading account not found")
    
    # Create trading action
    action = TradingAction(
        action_type=schema.action_type,
        instrument=schema.instrument,
        quantity=schema.quantity,
        price=schema.price,
        trade_value=schema.trade_value,
        order_type=schema.order_type,
        strategy_id=schema.strategy_id
    )
    
    # Validate against limits
    validator = get_trading_limit_validator()
    result = validator.validate_trading_action(
        current_user, trading_account, action, db
    )
    
    return TradingLimitValidationResultSchema(
        allowed=result.allowed,
        violations=result.violations,
        warnings=result.warnings,
        actions_required=result.actions_required,
        override_possible=result.override_possible,
        error_message=result.error_message,
        breaches_detected=[
            TradingLimitBreachResponseSchema.from_orm(breach) 
            for breach in result.breaches_detected
        ]
    )

@router.post("/reset-usage")
# @handle_service_errors
# @log_service_call
async def reset_trading_limit_usage(
    schema: TradingLimitUsageResetSchema,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset usage counters for trading limits"""
    
    limits = db.query(UserTradingLimit).filter(
        UserTradingLimit.id.in_(schema.limit_ids)
    ).all()
    
    if not limits:
        raise HTTPException(status_code=404, detail="No trading limits found")
    
    # Verify permissions for all limits
    for limit in limits:
        trading_account = db.query(TradingAccount).filter(
            TradingAccount.id == limit.trading_account_id
        ).first()
        organization = db.query(Organization).filter(
            Organization.id == trading_account.organization_id
        ).first()
        
        if organization.owner_id != int(current_user.user_id):
            raise HTTPException(
                status_code=403, 
                detail=f"No permission to reset limit {limit.id}"
            )
    
    # Reset usage for all limits
    for limit in limits:
        limit.reset_usage()
    
    db.commit()
    
    logger.info(f"Reset usage for {len(limits)} trading limits")
    return {"message": f"Usage reset for {len(limits)} trading limits"}

@router.get("/breaches", response_model=List[TradingLimitBreachResponseSchema])
# @handle_service_errors
# @log_service_call
async def list_trading_limit_breaches(
    user_id: Optional[int] = Query(None),
    trading_account_id: Optional[int] = Query(None),
    severity: Optional[str] = Query(None),
    resolved: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List trading limit breaches"""
    
    query = db.query(TradingLimitBreach)
    
    # Apply filters
    if user_id:
        query = query.filter(TradingLimitBreach.user_id == user_id)
    if trading_account_id:
        query = query.filter(TradingLimitBreach.trading_account_id == trading_account_id)
    if severity:
        query = query.filter(TradingLimitBreach.severity == severity)
    if resolved is not None:
        if resolved:
            query = query.filter(TradingLimitBreach.resolved_time.isnot(None))
        else:
            query = query.filter(TradingLimitBreach.resolved_time.is_(None))
    
    # Filter by organization access
    query = query.join(Organization).filter(
        Organization.owner_id == int(current_user.user_id)
    )
    
    breaches = query.order_by(TradingLimitBreach.breach_time.desc()).offset(skip).limit(limit).all()
    
    return [TradingLimitBreachResponseSchema.from_orm(breach) for breach in breaches]

@router.post("/bulk-create", response_model=List[TradingLimitResponseSchema])
# @handle_service_errors
# @log_service_call
# @track_performance
async def bulk_create_trading_limits(
    schema: BulkTradingLimitCreateSchema,
    current_user: UserContext = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create multiple trading limits in bulk"""
    
    created_limits = []
    
    for limit_schema in schema.limits:
        # Apply to all users if specified
        user_ids = []
        if schema.apply_to_all_users and schema.user_ids:
            user_ids = schema.user_ids
        else:
            user_ids = [limit_schema.user_id]
        
        for user_id in user_ids:
            # Verify permissions
            trading_account = db.query(TradingAccount).filter(
                TradingAccount.id == limit_schema.trading_account_id
            ).first()
            
            if not trading_account:
                continue
                
            organization = db.query(Organization).filter(
                Organization.id == trading_account.organization_id
            ).first()
            
            if not organization or organization.owner_id != int(current_user.user_id):
                continue
            
            # Create limit
            limit = UserTradingLimit(
                user_id=user_id,
                trading_account_id=limit_schema.trading_account_id,
                organization_id=trading_account.organization_id,
                strategy_id=limit_schema.strategy_id,
                limit_type=limit_schema.limit_type,
                limit_scope=limit_schema.limit_scope,
                enforcement_type=limit_schema.enforcement_type,
                limit_value=limit_schema.limit_value,
                limit_percentage=limit_schema.limit_percentage,
                limit_count=limit_schema.limit_count,
                limit_text=limit_schema.limit_text,
                start_time=limit_schema.start_time,
                end_time=limit_schema.end_time,
                allowed_days=limit_schema.allowed_days,
                usage_reset_frequency=limit_schema.usage_reset_frequency,
                override_allowed=limit_schema.override_allowed,
                warning_threshold=limit_schema.warning_threshold,
                notify_on_breach=limit_schema.notify_on_breach,
                set_by_id=int(current_user.user_id)
            )
            
            db.add(limit)
            created_limits.append(limit)
    
    db.commit()
    
    for limit in created_limits:
        db.refresh(limit)
    
    logger.info(f"Bulk created {len(created_limits)} trading limits")
    return [TradingLimitResponseSchema.from_orm(limit) for limit in created_limits]