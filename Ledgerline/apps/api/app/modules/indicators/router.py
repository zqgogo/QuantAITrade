from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.modules.indicators.schemas import (
    AvailableIndicatorsResponse,
    BollingerBandsResponse,
    EMAResponse,
    MACDResponse,
    MomentumResponse,
    ROCResponse,
    RSIResponse,
    SMAResponse,
    VolumeMAResponse,
)
from app.modules.indicators.service import indicator_service

router = APIRouter()


@router.get("/available", response_model=AvailableIndicatorsResponse)
async def get_available_indicators() -> AvailableIndicatorsResponse:
    return indicator_service.get_available_indicators()


@router.get("/sma", response_model=SMAResponse)
async def get_sma(
    market: str = Query(description="Market type"),
    symbol: str = Query(description="Trading symbol"),
    interval: str = Query(description="Time interval"),
    period: Optional[int] = Query(20, description="SMA period"),
) -> SMAResponse:
    return indicator_service.calculate_sma(market, symbol, interval, period)


@router.get("/ema", response_model=EMAResponse)
async def get_ema(
    market: str = Query(description="Market type"),
    symbol: str = Query(description="Trading symbol"),
    interval: str = Query(description="Time interval"),
    period: Optional[int] = Query(20, description="EMA period"),
) -> EMAResponse:
    return indicator_service.calculate_ema(market, symbol, interval, period)


@router.get("/macd", response_model=MACDResponse)
async def get_macd(
    market: str = Query(description="Market type"),
    symbol: str = Query(description="Trading symbol"),
    interval: str = Query(description="Time interval"),
    fast_period: Optional[int] = Query(12, description="Fast period"),
    slow_period: Optional[int] = Query(26, description="Slow period"),
    signal_period: Optional[int] = Query(9, description="Signal period"),
) -> MACDResponse:
    return indicator_service.calculate_macd(
        market, symbol, interval, fast_period, slow_period, signal_period
    )


@router.get("/rsi", response_model=RSIResponse)
async def get_rsi(
    market: str = Query(description="Market type"),
    symbol: str = Query(description="Trading symbol"),
    interval: str = Query(description="Time interval"),
    period: Optional[int] = Query(14, description="RSI period"),
) -> RSIResponse:
    return indicator_service.calculate_rsi(market, symbol, interval, period)


@router.get("/bollinger", response_model=BollingerBandsResponse)
async def get_bollinger_bands(
    market: str = Query(description="Market type"),
    symbol: str = Query(description="Trading symbol"),
    interval: str = Query(description="Time interval"),
    period: Optional[int] = Query(20, description="BB period"),
    num_std: Optional[float] = Query(2.0, description="Number of standard deviations"),
) -> BollingerBandsResponse:
    return indicator_service.calculate_bollinger_bands(market, symbol, interval, period, num_std)


@router.get("/momentum", response_model=MomentumResponse)
async def get_momentum(
    market: str = Query(description="Market type"),
    symbol: str = Query(description="Trading symbol"),
    interval: str = Query(description="Time interval"),
    period: Optional[int] = Query(10, description="Momentum period"),
) -> MomentumResponse:
    return indicator_service.calculate_momentum(market, symbol, interval, period)


@router.get("/roc", response_model=ROCResponse)
async def get_roc(
    market: str = Query(description="Market type"),
    symbol: str = Query(description="Trading symbol"),
    interval: str = Query(description="Time interval"),
    period: Optional[int] = Query(12, description="ROC period"),
) -> ROCResponse:
    return indicator_service.calculate_roc(market, symbol, interval, period)


@router.get("/volume-ma", response_model=VolumeMAResponse)
async def get_volume_ma(
    market: str = Query(description="Market type"),
    symbol: str = Query(description="Trading symbol"),
    interval: str = Query(description="Time interval"),
    period: Optional[int] = Query(20, description="Volume MA period"),
) -> VolumeMAResponse:
    return indicator_service.calculate_volume_ma(market, symbol, interval, period)


@router.get("/calculate")
async def calculate_indicator(
    market: str = Query(description="Market type"),
    symbol: str = Query(description="Trading symbol"),
    interval: str = Query(description="Time interval"),
    indicator: str = Query(description="Indicator name"),
    period: Optional[int] = Query(20),
    fast_period: Optional[int] = Query(12),
    slow_period: Optional[int] = Query(26),
    signal_period: Optional[int] = Query(9),
    num_std: Optional[float] = Query(2.0),
):
    try:
        return indicator_service.calculate_indicator(
            market=market,
            symbol=symbol,
            interval=interval,
            indicator=indicator,
            period=period,
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
            num_std=num_std,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
