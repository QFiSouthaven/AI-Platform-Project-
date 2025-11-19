"""
API v1 routes for Core Processing module.
"""

from fastapi import APIRouter

from app.api.v1 import generate, debug, optimize, evaluate

api_router = APIRouter()

api_router.include_router(
    generate.router,
    prefix="/generate",
    tags=["Code Generation"]
)
api_router.include_router(
    debug.router,
    prefix="/debug",
    tags=["Debugging"]
)
api_router.include_router(
    optimize.router,
    prefix="/optimize",
    tags=["Optimization"]
)
api_router.include_router(
    evaluate.router,
    prefix="/evaluate",
    tags=["Evaluation"]
)
