import sys
import os
import asyncio
import time
from fastapi import HTTPException, Response, Request
import json

# Ensure the parent folder (user_service/) is in the PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from sqlalchemy import text
from shared_architecture.utils.service_utils import start_service, stop_service
from shared_architecture.utils.logging_utils import log_info, log_exception
from shared_architecture.auth import init_jwt_manager
from shared_architecture.utils.keycloak_helper import init_keycloak_manager

# Imports for your specific microservice components
from app.api.endpoints import users, auth, groups, permissions  # Your API routes
from app.routers import trading_limits  # Trading limits API
from app.context.global_app import set_app  # For global app state
from app.core.config import settings as userServiceSettings  # Your custom settings class

# Import tasks to register them  
from app.tasks import (
    send_welcome_email, send_user_notification, 
    daily_user_analytics, weekly_user_cleanup
)
from app.monitoring.user_metrics import user_metrics

# Database models and table creation
from shared_architecture.db.models.user import Base as UserBase
from shared_architecture.db.models.group import Base as GroupBase
from shared_architecture.db.session import sync_engine

# Create tables (you might want to move this to a migration script)
try:
    UserBase.metadata.create_all(bind=sync_engine)
    GroupBase.metadata.create_all(bind=sync_engine)
    log_info("✅ Database tables created/verified")
except Exception as e:
    log_exception(f"❌ Failed to create database tables: {e}")

# Start the service with new service discovery system
app: FastAPI = start_service("user_service")
set_app(app)  # Set the app globally if needed by other parts of your shared architecture

# Include your API routers
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(groups.router, prefix="/groups", tags=["groups"])
app.include_router(trading_limits.router, tags=["trading-limits"])
app.include_router(permissions.router, prefix="/api/permissions", tags=["permissions"])


@app.on_event("startup")
async def custom_startup():
    """
    Custom startup logic for user service - runs after shared_architecture's infrastructure setup.
    Updated to work with new service discovery system.
    """
    log_info("🚀 user_service custom startup logic started.")
    
    # 1. Wait for infrastructure connections to be ready (populated by start_service)
    max_wait = 30  # seconds
    wait_interval = 1  # second
    waited = 0
    
    while waited < max_wait:
        # Check for connection manager initialization
        if (hasattr(app.state, 'connection_manager') and 
            hasattr(app.state, 'connections') and 
            app.state.connections.get("timescaledb")):
            log_info("✅ Infrastructure is ready, proceeding with service initialization")
            break
        log_info(f"⏳ Waiting for infrastructure... ({waited}s/{max_wait}s)")
        await asyncio.sleep(wait_interval)
        waited += wait_interval
    else:
        log_exception("❌ Infrastructure startup timeout - connections not ready.")
        raise Exception("Infrastructure startup timeout - connections not ready")
    
    # 2. Load microservice-specific settings
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            log_info(f"📝 Loading user service settings attempt {attempt + 1}/{max_retries}")
            
            # Use the settings instance directly (simplified approach)
            app.state.settings = userServiceSettings
            log_info("✅ User service settings loaded successfully.")

            # Get session factory with validation
            session_factory = app.state.connections.get("timescaledb")
            if not session_factory:
                raise Exception("TimescaleDB session factory not available in app.state.connections.")
            
            log_info(f"🔍 Database verification attempt {attempt + 1}/{max_retries}")
            
            # Test database connection
            async with session_factory() as session:
                try:
                    result = await session.execute(text("SELECT 1 as test"))
                    test_row = result.fetchone()
                    log_info(f"✅ Database connection test successful: {test_row[0]}")
                except Exception as conn_test_error:
                    log_exception(f"❌ Database connection test failed: {conn_test_error}")
                    raise  # Re-raise to trigger retry logic
                
                # Database is working, continue with service-specific initialization
                log_info("📊 Performing service-specific database checks...")
                
                # Example: Check if required tables exist
                try:
                    tables_check = await session.execute(text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name IN ('users', 'groups', 'activity_logs')
                    """))
                    existing_tables = [row[0] for row in tables_check.fetchall()]
                    log_info(f"📋 Found existing tables: {existing_tables}")
                except Exception as table_check_error:
                    log_exception(f"⚠️  Table check failed: {table_check_error}")
                
                break  # Success, exit retry loop
                    
        except Exception as e:
            if attempt < max_retries - 1:
                log_exception(f"❌ Startup attempt {attempt + 1} failed, retrying in {retry_delay}s: {e}")
                await asyncio.sleep(retry_delay)
                retry_delay *= 1.5  # Gradual backoff
                continue
            else:
                log_exception(f"❌ user_service initialization failed after {max_retries} attempts: {e}")
                raise

    # 3. Service health check and logging
    try:
        health_status = await app.state.connection_manager.health_check()
        healthy_services = [k for k, v in health_status.items() if v["status"] == "healthy"]
        degraded_services = [k for k, v in health_status.items() if v["status"] == "unavailable"]
        
        log_info(f"🟢 Healthy services: {healthy_services}")
        if degraded_services:
            log_info(f"🟡 Unavailable services (graceful degradation): {degraded_services}")
            
    except Exception as e:
        log_exception(f"❌ Health check failed: {e}")

    # 4. Initialize authentication and Keycloak managers
    try:
        log_info("🔧 Initializing authentication components...")
        
        # Initialize JWT manager
        keycloak_url = userServiceSettings.keycloak_url
        keycloak_realm = userServiceSettings.keycloak_realm
        keycloak_client_id = userServiceSettings.keycloak_client_id
        
        init_jwt_manager(keycloak_url, keycloak_realm, keycloak_client_id)
        log_info("✅ JWT manager initialized")
        
        # Initialize Keycloak manager if admin credentials are available
        try:
            keycloak_client_secret = getattr(userServiceSettings, 'keycloak_client_secret', "")
            keycloak_admin_username = getattr(userServiceSettings, 'keycloak_admin_username', "admin")
            keycloak_admin_password = getattr(userServiceSettings, 'keycloak_admin_password', "")
            
            if keycloak_admin_password:
                init_keycloak_manager(
                    keycloak_url,
                    keycloak_realm,
                    keycloak_client_id,
                    keycloak_client_secret,
                    keycloak_admin_username,
                    keycloak_admin_password
                )
                log_info("✅ Keycloak manager initialized")
            else:
                log_info("⚠️  Keycloak admin credentials not provided - user provisioning disabled")
                
        except Exception as kc_error:
            log_exception(f"⚠️  Keycloak manager initialization failed: {kc_error}")
            log_info("🔄 Continuing without Keycloak user provisioning")
        
        log_info("✅ Authentication components initialized")
    except Exception as e:
        log_exception(f"❌ Authentication initialization failed: {e}")
        # Continue without full auth - basic JWT validation might still work

    # 5. Initialize service integrations
    try:
        log_info("🔧 Initializing service integrations...")
        
        from shared_architecture.setup.service_integrations import setup_service_integrations, EXAMPLE_CONFIG
        
        # Load integration config (in production, this would come from environment/config file)
        integration_config = {
            "services": {
                "user_service": {"url": "http://localhost:8002"},
                "trade_service": {"url": "http://localhost:8004"},
                "service_secret": userServiceSettings.service_secret if hasattr(userServiceSettings, 'service_secret') else "default-secret"
            },
            "alerting": {
                "email": {"enabled": False},  # Disabled for development
                "slack": {"enabled": False},   # Disabled for development
                "sms": {"enabled": False}      # Disabled for development
            }
        }
        
        await setup_service_integrations(integration_config)
        log_info("✅ Service integrations initialized")
        
    except Exception as e:
        log_exception(f"⚠️  Service integrations initialization failed: {e}")
        log_info("🔄 Continuing without full integrations")

    log_info("✅ user_service custom startup complete.")


@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint using the new connection manager.
    """
    try:
        # Get health status from connection manager
        connection_health = await app.state.connection_manager.health_check()
        
        # Determine overall status
        overall_status = "healthy"
        for service, status in connection_health.items():
            if status["status"] == "unhealthy":
                overall_status = "unhealthy"
                break
            elif status["status"] == "unavailable" and overall_status != "unhealthy":
                overall_status = "degraded"
        
        # Add service-specific health checks
        health_status = {
            "overall_status": overall_status,
            "service": "user_service",
            "connections": connection_health,
            "custom_checks": {}
        }
        
        # Add custom microservice health checks
        try:
            if hasattr(app.state, 'auth_service'):
                health_status["custom_checks"]["auth_service"] = {"status": "healthy", "message": "Authentication service operational"}
        except Exception as e:
            health_status["custom_checks"]["auth_service"] = {"status": "unhealthy", "message": str(e)}
            if overall_status == "healthy":
                overall_status = "degraded"

        # Update overall status based on custom checks
        health_status["overall_status"] = overall_status

        # Return appropriate HTTP status code
        if overall_status == "unhealthy":
            raise HTTPException(status_code=500, detail=health_status)
        elif overall_status == "degraded":
            return Response(
                content=json.dumps(health_status),
                status_code=503,
                media_type="application/json"
            )

        return health_status
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        log_exception(f"❌ Health check failed: {e}")
        error_response = {
            "overall_status": "error",
            "service": "user_service", 
            "message": str(e)
        }
        raise HTTPException(status_code=500, detail=error_response)


@app.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check with more information about service discovery
    """
    try:
        from shared_architecture.connections.service_discovery import service_discovery, ServiceType
        
        connection_health = await app.state.connection_manager.health_check()
        
        detailed_health = {
            "service": "user_service",
            "environment": service_discovery.environment.value,
            "connections": connection_health,
            "service_discovery": {
                "redis": service_discovery.get_connection_info("redis", ServiceType.REDIS),
                "timescaledb": service_discovery.get_connection_info("timescaledb", ServiceType.TIMESCALEDB),
                "rabbitmq": service_discovery.get_connection_info("rabbitmq", ServiceType.RABBITMQ),
                "mongodb": service_discovery.get_connection_info("mongo", ServiceType.MONGODB),
            }
        }
        
        return detailed_health
        
    except Exception as e:
        log_exception(f"❌ Detailed health check failed: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})


@app.get("/health/integrations")
async def integration_health_check():
    """
    Check status of service integrations
    """
    try:
        from shared_architecture.setup.service_integrations import get_integration_status
        
        integration_status = get_integration_status()
        
        return {
            "service": "user_service",
            "integrations": integration_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        log_exception(f"❌ Integration health check failed: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})


# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Log request details (you can customize this)
    log_info(f"📥 {request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response


# Shutdown Event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Handles shutdown events: gracefully stops the service and closes connections.
    """
    log_info("🛑 User Service shutting down...")
    try:
        await stop_service("user_service")
        log_info("✅ User Service shutdown complete.")
    except Exception as e:
        log_exception(f"❌ Error during shutdown: {e}")


@app.get("/")
def read_root():
    return {"message": "Welcome to User Service", "service": "user_service", "status": "operational"}


# Main Runner (for local development or explicit run)
def run_uvicorn():
    import uvicorn
    log_info("🚀 Starting uvicorn server on 0.0.0.0:8002")
    uvicorn.run(
        app="app.main:app",
        host="0.0.0.0",
        port=8002,
        reload=False,  # Disabled for container compatibility and production
        access_log=True,
        log_level="info"
    )


# MINIMAL FIX: Only run uvicorn startup logic when NOT being imported by uvicorn
if __name__ == "__main__":
    try:
        # Check if we should start uvicorn based on config
        should_run_uvicorn = app.state.config.get("private", {}).get("RUN_UVICORN", False)
        if should_run_uvicorn:
            log_info('🎯 RUN_UVICORN is true. Starting uvicorn...')
            # Retry loop for uvicorn startup
            max_retries = 3
            retry_delay = 5
            for attempt in range(max_retries):
                try:
                    log_info(f"🔁 Attempt {attempt + 1} to start user_service via uvicorn...")
                    run_uvicorn()
                    break
                except Exception as e:
                    log_exception(f"❌ Uvicorn failed to start on attempt {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        log_info(f"⏳ Waiting {retry_delay} seconds before retry...")
                        time.sleep(retry_delay)
                        retry_delay *= 1.5
                    else:
                        log_info("❌ All uvicorn startup attempts failed.")
        else:
            log_info('🎯 RUN_UVICORN is false or not set. Starting uvicorn directly...')
            import uvicorn
            uvicorn.run(
                "app.main:app",
                host="0.0.0.0", 
                port=int(os.getenv("UVICORN_PORT", "8002")),
                reload=True,
                log_level="info"
            )
    except (KeyError, AttributeError, TypeError) as e:
        log_info(f'⚙️  Config not available, starting uvicorn with defaults: {e}')
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0", 
            port=8002,
            reload=True,
            log_level="info"
        )
else:
    # When imported by uvicorn (production), just log that we're ready
    log_info('✅ User service app created and ready for uvicorn startup.')