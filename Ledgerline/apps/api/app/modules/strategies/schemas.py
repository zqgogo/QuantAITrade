from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SignalType(str):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class Signal(BaseModel):
    signal_type: str = Field(description="Signal type: buy, sell, hold")
    strength: float = Field(description="Signal strength 0-1")
    confidence: float = Field(description="Confidence level 0-1")
    strategy: str = Field(description="Strategy that generated the signal")
    symbol: str = Field(description="Trading symbol")
    market: str = Field(description="Market type")
    interval: str = Field(description="Time interval")
    timestamp: datetime = Field(description="Signal generation time")
    message: Optional[str] = Field(None, description="Signal description")
    parameters: Optional[dict] = Field(None, description="Strategy parameters")


class StrategyRunRequest(BaseModel):
    market: str = Field(description="Market type")
    symbol: str = Field(description="Trading symbol")
    interval: str = Field(description="Time interval")
    strategy: str = Field(description="Strategy name")
    parameters: Optional[dict] = Field(None, description="Strategy parameters")


class StrategyRunResponse(BaseModel):
    success: bool = Field(description="Whether the strategy ran successfully")
    signal: Optional[Signal] = Field(None, description="Generated signal")
    message: Optional[str] = Field(None, description="Result message")


class StrategyInfo(BaseModel):
    name: str = Field(description="Strategy name")
    description: str = Field(description="Strategy description")
    parameters: List[dict] = Field(description="Available parameters")
    default_parameters: dict = Field(description="Default parameters")


class AvailableStrategiesResponse(BaseModel):
    strategies: List[StrategyInfo] = Field(description="List of available strategies")


class MultiStrategyRunRequest(BaseModel):
    market: str = Field(description="Market type")
    symbol: str = Field(description="Trading symbol")
    interval: str = Field(description="Time interval")
    strategies: List[str] = Field(description="List of strategy names")
    parameters: Optional[dict] = Field(None, description="Common parameters")


class MultiStrategyRunResponse(BaseModel):
    signals: List[Signal] = Field(description="List of signals from all strategies")
    summary: dict = Field(description="Summary of all signals")
