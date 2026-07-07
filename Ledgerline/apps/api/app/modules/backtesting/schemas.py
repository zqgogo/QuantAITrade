from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    strategy_name: str = Field(description="Strategy name to backtest")
    market: str = Field(description="Market type")
    symbol: str = Field(description="Trading symbol")
    interval: str = Field(description="Time interval")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    initial_capital: float = Field(10000, description="Initial capital")
    position_size: float = Field(0.02, description="Position size as fraction of capital")
    commission_rate: float = Field(0.001, description="Commission rate per trade")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Strategy parameters")


class TradeRecord(BaseModel):
    timestamp: datetime = Field(description="Trade execution time")
    type: str = Field(description="Trade type: buy or sell")
    price: float = Field(description="Trade price")
    quantity: float = Field(description="Trade quantity")
    amount: float = Field(description="Trade amount")
    commission: float = Field(description="Commission paid")
    balance: float = Field(description="Account balance after trade")
    pnl: float = Field(description="Profit/loss since last trade")
    pnl_cumulative: float = Field(description="Cumulative profit/loss")


class PerformanceMetrics(BaseModel):
    total_return: float = Field(description="Total return percentage")
    annualized_return: float = Field(description="Annualized return percentage")
    max_drawdown: float = Field(description="Maximum drawdown percentage")
    sharpe_ratio: float = Field(description="Sharpe ratio")
    sortino_ratio: float = Field(description="Sortino ratio")
    win_rate: float = Field(description="Win rate percentage")
    profit_factor: float = Field(description="Profit factor")
    total_trades: int = Field(description="Total number of trades")
    winning_trades: int = Field(description="Number of winning trades")
    losing_trades: int = Field(description="Number of losing trades")
    avg_win: float = Field(description="Average winning trade")
    avg_loss: float = Field(description="Average losing trade")
    best_trade: float = Field(description="Best trade return")
    worst_trade: float = Field(description="Worst trade return")


class EquityCurvePoint(BaseModel):
    timestamp: datetime = Field(description="Time point")
    equity: float = Field(description="Account equity")
    returns: float = Field(description="Period return")


class BacktestResult(BaseModel):
    success: bool = Field(description="Whether backtest succeeded")
    message: str = Field(description="Result message")
    strategy_name: str = Field(description="Strategy name")
    symbol: str = Field(description="Trading symbol")
    interval: str = Field(description="Time interval")
    start_date: datetime = Field(description="Backtest start date")
    end_date: datetime = Field(description="Backtest end date")
    initial_capital: float = Field(description="Initial capital")
    final_capital: float = Field(description="Final capital")
    duration_days: int = Field(description="Backtest duration in days")
    metrics: PerformanceMetrics = Field(description="Performance metrics")
    trades: List[TradeRecord] = Field(description="List of trades")
    equity_curve: List[EquityCurvePoint] = Field(description="Equity curve data")


class BacktestSummary(BaseModel):
    strategy_name: str = Field(description="Strategy name")
    total_return: float = Field(description="Total return")
    max_drawdown: float = Field(description="Max drawdown")
    sharpe_ratio: float = Field(description="Sharpe ratio")
    win_rate: float = Field(description="Win rate")
    total_trades: int = Field(description="Total trades")


class BacktestListResponse(BaseModel):
    backtests: List[BacktestSummary] = Field(description="List of recent backtests")
