from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query

from app.modules.market.schemas import (
    DataProgressResponse,
    MarketStatusResponse,
    OhlcvResponse,
    PriceResponse,
    RefreshResponse,
)
from app.modules.market.service import market_service

router = APIRouter()


@router.get("/status", response_model=MarketStatusResponse)
async def market_status() -> MarketStatusResponse:
    return MarketStatusResponse(
        module="market",
        status="operational",
        exchange="mock",
        supported_intervals=["1m", "5m", "15m", "1h", "4h", "1d"],
    )


@router.get("/ohlcv", response_model=OhlcvResponse)
async def get_ohlcv(
    market: str = Query(description="Market type (crypto, stock, futures)"),
    symbol: str = Query(description="Trading symbol (e.g., BTC/USDT)"),
    interval: str = Query(description="Time interval (1m, 5m, 15m, 1h, 4h, 1d)"),
    start_time: Optional[datetime] = Query(None, description="Start time"),
    end_time: Optional[datetime] = Query(None, description="End time"),
    limit: Optional[int] = Query(100, description="Maximum bars to return"),
) -> OhlcvResponse:
    return market_service.get_ohlcv(
        market=market,
        symbol=symbol,
        interval=interval,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )


@router.post("/ohlcv/refresh", response_model=RefreshResponse)
async def refresh_ohlcv(
    market: str = Query(description="Market type"),
    symbol: str = Query(description="Trading symbol"),
    interval: str = Query(description="Time interval"),
    limit: Optional[int] = Query(100, description="Number of bars to fetch"),
) -> RefreshResponse:
    return market_service.refresh_ohlcv(
        market=market,
        symbol=symbol,
        interval=interval,
        limit=limit,
    )


@router.get("/price", response_model=PriceResponse)
async def get_price(
    market: str = Query(description="Market type"),
    symbol: str = Query(description="Trading symbol"),
) -> PriceResponse:
    return market_service.get_current_price(
        market=market,
        symbol=symbol,
    )


@router.get("/progress", response_model=DataProgressResponse)
async def get_data_progress(
    market: str = Query(description="Market type"),
    symbol: str = Query(description="Trading symbol"),
    interval: str = Query(description="Time interval"),
) -> DataProgressResponse:
    return market_service.get_data_progress(
        market=market,
        symbol=symbol,
        interval=interval,
    )
