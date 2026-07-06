from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.modules.strategies.schemas import (
    AvailableStrategiesResponse,
    MultiStrategyRunResponse,
    StrategyRunResponse,
)
from app.modules.strategies.service import strategy_service

router = APIRouter()


@router.get("/available", response_model=AvailableStrategiesResponse)
async def get_available_strategies() -> AvailableStrategiesResponse:
    return strategy_service.get_available_strategies()


@router.post("/run", response_model=StrategyRunResponse)
async def run_strategy(
    market: str = Query(description="Market type"),
    symbol: str = Query(description="Trading symbol"),
    interval: str = Query(description="Time interval"),
    strategy: str = Query(description="Strategy name"),
    period: Optional[int] = Query(None, description="Strategy period"),
    fast_period: Optional[int] = Query(None, description="Fast period for MACD"),
    slow_period: Optional[int] = Query(None, description="Slow period for MACD"),
    signal_period: Optional[int] = Query(None, description="Signal period for MACD"),
    short_period: Optional[int] = Query(None, description="Short period for MA cross"),
    long_period: Optional[int] = Query(None, description="Long period for MA cross"),
    ma_type: Optional[str] = Query(None, description="MA type: sma or ema"),
    oversold_threshold: Optional[float] = Query(None, description="Oversold threshold for RSI"),
    overbought_threshold: Optional[float] = Query(None, description="Overbought threshold for RSI"),
    num_std: Optional[float] = Query(None, description="Number of standard deviations for BB"),
) -> StrategyRunResponse:
    parameters = {}
    if period is not None:
        parameters["period"] = period
    if fast_period is not None:
        parameters["fast_period"] = fast_period
    if slow_period is not None:
        parameters["slow_period"] = slow_period
    if signal_period is not None:
        parameters["signal_period"] = signal_period
    if short_period is not None:
        parameters["short_period"] = short_period
    if long_period is not None:
        parameters["long_period"] = long_period
    if ma_type is not None:
        parameters["ma_type"] = ma_type
    if oversold_threshold is not None:
        parameters["oversold_threshold"] = oversold_threshold
    if overbought_threshold is not None:
        parameters["overbought_threshold"] = overbought_threshold
    if num_std is not None:
        parameters["num_std"] = num_std

    return strategy_service.run_strategy(market, symbol, interval, strategy, parameters)


@router.post("/run/multiple", response_model=MultiStrategyRunResponse)
async def run_multiple_strategies(
    market: str = Query(description="Market type"),
    symbol: str = Query(description="Trading symbol"),
    interval: str = Query(description="Time interval"),
    strategies: List[str] = Query(description="List of strategy names"),
    period: Optional[int] = Query(None, description="Default period"),
) -> MultiStrategyRunResponse:
    parameters = {}
    if period is not None:
        parameters["period"] = period

    return strategy_service.run_multiple_strategies(market, symbol, interval, strategies, parameters)


@router.get("/run/{strategy_name}", response_model=StrategyRunResponse)
async def run_strategy_by_name(
    strategy_name: str,
    market: str = Query(description="Market type"),
    symbol: str = Query(description="Trading symbol"),
    interval: str = Query(description="Time interval"),
    period: Optional[int] = Query(None),
) -> StrategyRunResponse:
    parameters = {}
    if period is not None:
        parameters["period"] = period

    return strategy_service.run_strategy(market, symbol, interval, strategy_name, parameters)
