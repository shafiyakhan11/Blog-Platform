from .admin import router as admin_router
from .auth import router as auth_router

__all__ = ["auth_router", "admin_router"]
