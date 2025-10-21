from fastapi import APIRouter
from app.api.v1 import files, sessions, operations, images

api_router = APIRouter()

api_router.include_router(files.router)
api_router.include_router(sessions.router)
api_router.include_router(sessions.direct_router)
api_router.include_router(operations.router)
api_router.include_router(images.router)