from typing import List, Optional

from pydantic import BaseModel, Field


class IndicatorValue(BaseModel):
    timestamp: str
    value: Optional[float] = None


class SMAResponse(BaseModel):
    indicator: str = "SMA"
    period: int
    values: List[IndicatorValue]


class EMAResponse(BaseModel):
    indicator: str = "EMA"
    period: int
    values: List[IndicatorValue]


class MACDResponse(BaseModel):
    indicator: str = "MACD"
    fast_period: int
    slow_period: int
    signal_period: int
    macd_line: List[IndicatorValue]
    signal_line: List[IndicatorValue]
    histogram: List[IndicatorValue]


class RSIResponse(BaseModel):
    indicator: str = "RSI"
    period: int
    values: List[IndicatorValue]


class BollingerBandsResponse(BaseModel):
    indicator: str = "Bollinger Bands"
    period: int
    num_std: float
    upper_band: List[IndicatorValue]
    middle_band: List[IndicatorValue]
    lower_band: List[IndicatorValue]


class MomentumResponse(BaseModel):
    indicator: str = "Momentum"
    period: int
    values: List[IndicatorValue]


class ROCResponse(BaseModel):
    indicator: str = "ROC"
    period: int
    values: List[IndicatorValue]


class VolumeMAResponse(BaseModel):
    indicator: str = "Volume MA"
    period: int
    values: List[IndicatorValue]


class IndicatorRequest(BaseModel):
    market: str = Field(description="Market type (crypto, stock, futures)")
    symbol: str = Field(description="Trading symbol")
    interval: str = Field(description="Time interval")
    indicator: str = Field(description="Indicator name (SMA, EMA, MACD, RSI, BB, MOM, ROC, VOLUME_MA)")
    period: Optional[int] = Field(20, description="Indicator period")
    fast_period: Optional[int] = Field(12, description="Fast period for MACD")
    slow_period: Optional[int] = Field(26, description="Slow period for MACD")
    signal_period: Optional[int] = Field(9, description="Signal period for MACD")
    num_std: Optional[float] = Field(2.0, description="Number of standard deviations for Bollinger Bands")


class AvailableIndicatorsResponse(BaseModel):
    indicators: List[dict] = Field(description="List of available indicators")


class MultiIndicatorRequest(BaseModel):
    market: str = Field(description="Market type")
    symbol: str = Field(description="Trading symbol")
    interval: str = Field(description="Time interval")
    indicators: List[str] = Field(description="List of indicator names")
    period: Optional[int] = Field(20, description="Default period")
