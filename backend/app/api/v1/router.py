from fastapi import APIRouter
from app.api.v1.endpoints import calendar, optimization, admin, auth, tasks

api_router = APIRouter()

# Calendar routes (mixed prefixes, so mounted at root)
api_router.include_router(calendar.router, tags=["calendar"])

# Optimization routes (mixed prefixes, so mounted at root)
api_router.include_router(optimization.router, tags=["optimization"])

# Admin routes (consistent /admin prefix)
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

# Auth routes (mounted at root)
api_router.include_router(auth.router, tags=["auth"])

# Task routes (mounted at root)
api_router.include_router(tasks.router, tags=["tasks"])
