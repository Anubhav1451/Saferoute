# app/api/v1/__init__.py
from fastapi import APIRouter
from .routing import router as routing_router
from .sos import router as sos_router
from .ai import router as ai_router

api_router = APIRouter()
api_router.include_router(routing_router)
api_router.include_router(sos_router)
api_router.include_router(ai_router)

__all__ = ["api_router"]