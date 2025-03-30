# Marks the `endpoints` directory as a package
from .users import router as users_router
from .auth import router as auth_router
from .groups import router as groups_router

__all__ = ["users_router", "auth_router", "groups_router"]