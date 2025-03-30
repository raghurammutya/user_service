from fastapi import FastAPI
from app.api.endpoints import users, auth, groups
from app.core.events import startup_event, shutdown_event

app = FastAPI(title="User Service")

# Register routers
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(groups.router, prefix="/groups", tags=["groups"])

# Register startup/shutdown events
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)

@app.get("/")
def read_root():
    return {"message": "Welcome to User Service"}