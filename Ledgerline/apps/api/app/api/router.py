from fastapi import APIRouter

from app.modules.ai.router import router as ai_router
from app.modules.backtesting.router import router as backtesting_router
from app.modules.indicators.router import router as indicators_router
from app.modules.market.router import router as market_router
from app.modules.monitoring.router import router as monitoring_router
from app.modules.strategies.router import router as strategies_router
from app.modules.trading.router import router as trading_router

api_router = APIRouter()
api_router.include_router(trading_router, prefix="/trading", tags=["trading"])
api_router.include_router(market_router, prefix="/market", tags=["market"])
api_router.include_router(indicators_router, prefix="/indicators", tags=["indicators"])
api_router.include_router(strategies_router, prefix="/strategies", tags=["strategies"])
api_router.include_router(backtesting_router, prefix="/backtesting", tags=["backtesting"])
api_router.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])

