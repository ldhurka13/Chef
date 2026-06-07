"""
API Routers for the Chef application.

Available routers:
- auth: Authentication endpoints (/auth/*)

To include a router in main server.py:
    from routers.auth import router as auth_router
    api_router.include_router(auth_router)
"""
from routers.auth import router as auth_router

__all__ = ["auth_router"]
