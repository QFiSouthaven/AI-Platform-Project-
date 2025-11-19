"""
API v1 endpoints for the Data Integration module.
"""

from fastapi import APIRouter

from app.api.v1.events import router as events_router
from app.api.v1.cache import router as cache_router

api_router = APIRouter()
api_router.include_router(events_router, prefix="/events", tags=["events"])
api_router.include_router(cache_router, prefix="/cache", tags=["cache"])

__all__ = ["api_router"]
