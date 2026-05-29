from fastapi import APIRouter

from app.api.backtests import router as backtests_router
from app.api.dashboard import router as dashboard_router
from app.api.health import router as health_router
from app.api.operations import router as operations_router
from app.api.reviews import router as reviews_router
from app.api.signals import router as signals_router
from app.api.stock_pool import router as stock_pool_router

api_router = APIRouter()
api_router.include_router(backtests_router)
api_router.include_router(dashboard_router)
api_router.include_router(health_router)
api_router.include_router(operations_router)
api_router.include_router(reviews_router)
api_router.include_router(signals_router)
api_router.include_router(stock_pool_router)
