# user_service/app/monitoring/user_metrics.py
"""
User service specific metrics collection and monitoring.
Extends shared_architecture monitoring capabilities.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from shared_architecture.monitoring.metrics_collector import MetricsCollector, MetricType
from shared_architecture.utils.enhanced_logging import get_logger
from shared_architecture.utils.service_decorators import with_metrics

logger = get_logger(__name__)

class UserServiceMetrics:
    """User service specific metrics collection"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector.get_instance()
        self._setup_custom_metrics()
    
    def _setup_custom_metrics(self):
        """Setup user service specific metrics"""
        
        # User lifecycle metrics
        self.user_registrations = self.metrics_collector.counter(
            "user_registrations_total",
            "Total number of user registrations",
            tags={"service": "user_service"}
        )
        
        self.user_deletions = self.metrics_collector.counter(
            "user_deletions_total", 
            "Total number of user deletions",
            tags={"service": "user_service"}
        )
        
        self.user_updates = self.metrics_collector.counter(
            "user_updates_total",
            "Total number of user updates", 
            tags={"service": "user_service"}
        )
        
        # Authentication metrics
        self.login_attempts = self.metrics_collector.counter(
            "login_attempts_total",
            "Total login attempts",
            tags={"service": "user_service"}
        )
        
        self.login_successes = self.metrics_collector.counter(
            "login_successes_total",
            "Successful login attempts",
            tags={"service": "user_service"}
        )
        
        self.login_failures = self.metrics_collector.counter(
            "login_failures_total", 
            "Failed login attempts",
            tags={"service": "user_service"}
        )
        
        # Group metrics
        self.group_creations = self.metrics_collector.counter(
            "group_creations_total",
            "Total group creations",
            tags={"service": "user_service"}
        )
        
        self.group_member_additions = self.metrics_collector.counter(
            "group_member_additions_total",
            "Total group member additions",
            tags={"service": "user_service"}
        )
        
        # Performance metrics
        self.operation_duration = self.metrics_collector.histogram(
            "user_operation_duration_seconds",
            "Duration of user operations",
            tags={"service": "user_service"}
        )
        
        # Business metrics
        self.active_users_gauge = self.metrics_collector.gauge(
            "active_users_current",
            "Current number of active users",
            tags={"service": "user_service"}
        )
        
        self.total_users_gauge = self.metrics_collector.gauge(
            "total_users_current", 
            "Current total number of users",
            tags={"service": "user_service"}
        )
        
        # Error metrics
        self.validation_errors = self.metrics_collector.counter(
            "validation_errors_total",
            "Total validation errors",
            tags={"service": "user_service"}
        )
        
        self.database_errors = self.metrics_collector.counter(
            "database_errors_total",
            "Total database errors", 
            tags={"service": "user_service"}
        )
    
    def track_user_registration(self, user_role: str = "unknown", source: str = "api"):
        """Track user registration"""
        self.user_registrations.increment(tags={
            "role": user_role,
            "source": source
        })
        logger.info("User registration tracked", role=user_role, source=source)
    
    def track_user_login(self, success: bool, provider: str = "local", user_role: str = "unknown"):
        """Track user login attempt"""
        self.login_attempts.increment(tags={
            "provider": provider,
            "role": user_role
        })
        
        if success:
            self.login_successes.increment(tags={
                "provider": provider,
                "role": user_role
            })
        else:
            self.login_failures.increment(tags={
                "provider": provider,
                "role": user_role
            })
        
        logger.info("User login tracked", success=success, provider=provider, role=user_role)
    
    def track_group_operation(self, operation: str, success: bool):
        """Track group operations"""
        if operation == "create":
            self.group_creations.increment(tags={\"success\": str(success)})
        elif operation == "add_member":
            self.group_member_additions.increment(tags={\"success\": str(success)})
        
        logger.info("Group operation tracked", operation=operation, success=success)
    
    def track_operation_duration(self, operation: str, duration_seconds: float):
        """Track operation duration"""
        self.operation_duration.observe(duration_seconds, tags={
            "operation": operation
        })
        
        logger.debug("Operation duration tracked", operation=operation, duration=duration_seconds)
    
    def track_validation_error(self, field_name: str, error_type: str):
        """Track validation errors"""
        self.validation_errors.increment(tags={
            "field": field_name,
            "error_type": error_type
        })
        
        logger.warning("Validation error tracked", field=field_name, error_type=error_type)
    
    def track_database_error(self, operation: str, table: str, error_type: str):
        """Track database errors"""
        self.database_errors.increment(tags={
            "operation": operation,
            "table": table,
            "error_type": error_type
        })
        
        logger.error("Database error tracked", operation=operation, table=table, error_type=error_type)
    
    def update_user_counts(self, total_users: int, active_users: int):
        """Update user count gauges"""
        self.total_users_gauge.set(total_users)
        self.active_users_gauge.set(active_users)
        
        logger.info("User counts updated", total=total_users, active=active_users)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary for health checks"""
        try:
            return {
                "user_registrations": self.user_registrations.value,
                "login_attempts": self.login_attempts.value,
                "login_success_rate": self._calculate_success_rate(
                    self.login_successes.value,
                    self.login_attempts.value
                ),
                "group_creations": self.group_creations.value,
                "validation_errors": self.validation_errors.value,
                "database_errors": self.database_errors.value,
                "total_users": self.total_users_gauge.value,
                "active_users": self.active_users_gauge.value
            }
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {"error": "Failed to retrieve metrics"}
    
    def _calculate_success_rate(self, successes: int, total: int) -> float:
        """Calculate success rate percentage"""
        if total == 0:
            return 0.0
        return round((successes / total) * 100, 2)

# Global metrics instance
user_metrics = UserServiceMetrics()

# Decorator for automatic metrics tracking
def track_user_operation(operation_name: str):
    """Decorator to automatically track user operation metrics"""
    def decorator(func):
        @with_metrics(f"user_service_{operation_name}")
        async def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            
            try:
                result = await func(*args, **kwargs)
                
                # Track success
                duration = (datetime.utcnow() - start_time).total_seconds()
                user_metrics.track_operation_duration(operation_name, duration)
                
                return result
                
            except Exception as e:
                # Track failure
                duration = (datetime.utcnow() - start_time).total_seconds()
                user_metrics.track_operation_duration(f"{operation_name}_failed", duration)
                raise
        
        return wrapper
    return decorator