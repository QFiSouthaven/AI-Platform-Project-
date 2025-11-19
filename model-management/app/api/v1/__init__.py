"""
API v1 endpoints for Model Management.
"""

from fastapi import APIRouter

from app.api.v1 import models, plugins, versions

api_router = APIRouter()

api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(plugins.router, prefix="/plugins", tags=["plugins"])
api_router.include_router(versions.router, prefix="/versions", tags=["versions"])
