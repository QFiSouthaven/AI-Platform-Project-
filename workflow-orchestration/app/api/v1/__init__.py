"""
API v1 package for the Workflow Orchestration module.
"""

from fastapi import APIRouter

from app.api.v1.workflows import router as workflows_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.executions import router as executions_router

api_router = APIRouter()

api_router.include_router(workflows_router, prefix="/workflows", tags=["workflows"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(executions_router, prefix="/executions", tags=["executions"])
