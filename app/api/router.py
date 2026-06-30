from fastapi import APIRouter

from .exec import router as exec_router
from .workspace import router as workspace_router

api_router = APIRouter(prefix="/api")
api_router.include_router(exec_router, tags=["exec"])
api_router.include_router(workspace_router, tags=["workspace"])
