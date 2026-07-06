from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class OhlcvRequest(BaseModel):
    market: str = Field(description="Market type (crypto, stock, futures, etc.)")
    symbol: str = Field(description="Trading symbol (e.g., BTC/USDT, BTCUSDT)")
    interval: str = Field(description="Time interval (1m, 5m, 15m, 1h, 4h, 1d)")
    start_time: Optional[datetime] = Field(None, description="Start time for historical data")
    end_time: Optional[datetime] = Field(None, description="End time for historical data")
    limit: Optional[int] = Field(100, description="Maximum number of bars to return")


class OhlcvBarResponse(BaseModel):
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class OhlcvResponse(BaseModel):
    market: str
    symbol: str
    interval: str
    bars: List[OhlcvBarResponse]


class RefreshRequest(BaseModel):
    market: str = Field(description="Market type")
    symbol: str = Field(description="Trading symbol")
    interval: str = Field(description="Time interval")


class RefreshResponse(BaseModel):
    success: bool
    message: str
    fetched_count: int
    inserted_count: int


class PriceResponse(BaseModel):
    market: str
    symbol: str
    price: float
    timestamp: datetime


class MarketStatusResponse(BaseModel):
    module: str
    status: str
    exchange: Optional[str] = None
    supported_intervals: List[str] = ["1m", "5m", "15m", "1h", "4h", "1d"]


class DataProgressResponse(BaseModel):
    market: str
    symbol: str
    interval: str
    last_fetch_time: Optional[datetime] = None
    total_bars: int = 0
    earliest_time: Optional[datetime] = None
    latest_time: Optional[datetime] = None
