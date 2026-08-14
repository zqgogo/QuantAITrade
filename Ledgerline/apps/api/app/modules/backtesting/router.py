from typing import List

from fastapi import APIRouter, Body, Query

from app.modules.backtesting.schemas import BacktestRequest, BacktestResult, BacktestListResponse
from app.modules.backtesting.service import backtest_service
from app.modules.strategies.strategies import StrategyRegistry

router = APIRouter()


@router.post("/run", response_model=BacktestResult)
async def run_backtest(request: BacktestRequest = Body(description="Backtest request")) -> BacktestResult:
    return backtest_service.run_backtest(request)


@router.post("/run/multiple", response_model=List[BacktestResult])
async def run_multiple_backtests(
    strategies: List[str] = Query(description="List of strategy names"),
    market: str = Query(description="Market type"),
    symbol: str = Query(description="Trading symbol"),
    interval: str = Query(description="Time interval"),
    initial_capital: float = Query(10000, description="Initial capital"),
) -> List[BacktestResult]:
    return backtest_service.run_multiple_backtests(strategies, market, symbol, interval, initial_capital)


@router.get("/strategies", response_model=List[str])
async def get_available_strategies() -> List[str]:
    strategies = StrategyRegistry.get_all_strategies()
    return [s.name for s in strategies]


@router.get("/results", response_model=BacktestListResponse)
async def get_recent_backtests() -> BacktestListResponse:
    return BacktestListResponse(backtests=[])


@router.post("/quick-run", response_model=BacktestResult)
async def quick_run_backtest(
    strategy: str = Query(description="Strategy name"),
    market: str = Query(description="Market type"),
    symbol: str = Query(description="Trading symbol"),
    interval: str = Query(description="Time interval"),
    initial_capital: float = Query(10000, description="Initial capital"),
    position_size: float = Query(0.02, description="Position size"),
    commission_rate: float = Query(0.001, description="Commission rate"),
) -> BacktestResult:
    request = BacktestRequest(
        strategy_name=strategy,
        market=market,
        symbol=symbol,
        interval=interval,
        initial_capital=initial_capital,
        position_size=position_size,
        commission_rate=commission_rate,
    )
    return backtest_service.run_backtest(request)
