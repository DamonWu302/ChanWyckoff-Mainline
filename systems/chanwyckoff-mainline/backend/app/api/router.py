from fastapi import APIRouter

from app.api.dashboard import router as dashboard_router
from app.api.health import router as health_router
from app.api.reviews import router as reviews_router
from app.api.signals import router as signals_router

api_router = APIRouter()
api_router.include_router(dashboard_router)
api_router.include_router(health_router)
api_router.include_router(reviews_router)
api_router.include_router(signals_router)
