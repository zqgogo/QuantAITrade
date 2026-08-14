from datetime import datetime
from typing import List

from app.modules.backtesting.engine import BacktestEngine, PerformanceCalculator
from app.modules.backtesting.schemas import BacktestRequest, BacktestResult
from app.modules.market.repository import OhlcvRepository
from app.modules.strategies.strategies import StrategyRegistry


class BacktestService:
    def __init__(self):
        self.ohlcv_repository = OhlcvRepository()
    
    def run_backtest(self, request: BacktestRequest) -> BacktestResult:
        strategy = StrategyRegistry.get_strategy(request.strategy_name)
        
        if not strategy:
            return BacktestResult(
                success=False,
                message=f"Strategy '{request.strategy_name}' not found",
                strategy_name=request.strategy_name,
                symbol=request.symbol,
                interval=request.interval,
                start_date=datetime.now(),
                end_date=datetime.now(),
                initial_capital=request.initial_capital,
                final_capital=request.initial_capital,
                duration_days=0,
                metrics=PerformanceCalculator.calculate_metrics([], [], request.initial_capital, datetime.now(), datetime.now()),
                trades=[],
                equity_curve=[],
            )
        
        bars = self.ohlcv_repository.get_ohlcv(request.market, request.symbol, request.interval)
        
        if not bars:
            return BacktestResult(
                success=False,
                message="No OHLCV data available for backtesting",
                strategy_name=request.strategy_name,
                symbol=request.symbol,
                interval=request.interval,
                start_date=datetime.now(),
                end_date=datetime.now(),
                initial_capital=request.initial_capital,
                final_capital=request.initial_capital,
                duration_days=0,
                metrics=PerformanceCalculator.calculate_metrics([], [], request.initial_capital, datetime.now(), datetime.now()),
                trades=[],
                equity_curve=[],
            )
        
        prices = [float(bar.close) for bar in bars]
        volumes = [float(bar.volume) for bar in bars]
        timestamps = [bar.open_time for bar in bars]
        
        params = {**strategy.default_parameters, **(request.parameters or {})}
        
        engine = BacktestEngine()
        engine.initialize(
            initial_capital=request.initial_capital,
            commission_rate=request.commission_rate,
            position_size=request.position_size,
        )
        
        engine.update_equity(prices[0], timestamps[0])
        
        for i in range(len(prices)):
            signal = strategy.run(prices[:i+1], volumes[:i+1], **params)
            
            if signal and signal.signal_type in ["buy", "sell"]:
                engine.execute_trade(timestamps[i], signal.signal_type, prices[i])
            
            engine.update_equity(prices[i], timestamps[i])
        
        start_date = timestamps[0]
        end_date = timestamps[-1]
        duration_days = (end_date - start_date).days
        
        metrics = PerformanceCalculator.calculate_metrics(
            engine.trades,
            engine.equity_curve,
            request.initial_capital,
            start_date,
            end_date,
        )
        
        return BacktestResult(
            success=True,
            message=f"Backtest completed successfully with {len(engine.trades)//2} trades",
            strategy_name=request.strategy_name,
            symbol=request.symbol,
            interval=request.interval,
            start_date=start_date,
            end_date=end_date,
            initial_capital=request.initial_capital,
            final_capital=round(engine.equity, 2),
            duration_days=duration_days,
            metrics=metrics,
            trades=engine.trades,
            equity_curve=engine.equity_curve,
        )
    
    def run_multiple_backtests(
        self,
        strategy_names: List[str],
        market: str,
        symbol: str,
        interval: str,
        initial_capital: float = 10000,
    ) -> List[BacktestResult]:
        results = []
        for name in strategy_names:
            request = BacktestRequest(
                strategy_name=name,
                market=market,
                symbol=symbol,
                interval=interval,
                initial_capital=initial_capital,
            )
            result = self.run_backtest(request)
            results.append(result)
        return results


backtest_service = BacktestService()
