from datetime import datetime
from decimal import Decimal
from typing import List

from sqlalchemy import select

from app.db.session import TradingSessionLocal
from app.modules.backtesting.engine import BacktestEngine, PerformanceCalculator
from app.modules.backtesting.models import BacktestRecord
from app.modules.backtesting.schemas import BacktestRequest, BacktestResult, BacktestSummary
from app.modules.market.repository import OhlcvRepository
from app.modules.strategies.strategies import StrategyRegistry


class BacktestService:
    def __init__(self):
        self.ohlcv_repository = OhlcvRepository()

    def _save_result(self, result: BacktestResult) -> None:
        db = TradingSessionLocal()
        try:
            record = BacktestRecord(
                strategy_name=result.strategy_name,
                symbol=result.symbol,
                interval=result.interval,
                success=result.success,
                initial_capital=Decimal(str(result.initial_capital)),
                final_capital=Decimal(str(result.final_capital)),
                total_return=result.metrics.total_return,
                max_drawdown=result.metrics.max_drawdown,
                sharpe_ratio=result.metrics.sharpe_ratio,
                win_rate=result.metrics.win_rate,
                total_trades=result.metrics.total_trades,
                start_date=result.start_date,
                end_date=result.end_date,
            )
            db.add(record)
            db.commit()
        finally:
            db.close()

    def get_recent_results(self, limit: int = 20) -> List[BacktestSummary]:
        db = TradingSessionLocal()
        try:
            records = db.execute(
                select(BacktestRecord)
                .order_by(BacktestRecord.created_at.desc())
                .limit(limit)
            ).scalars().all()
            return [
                BacktestSummary(
                    strategy_name=record.strategy_name,
                    total_return=record.total_return,
                    max_drawdown=record.max_drawdown,
                    sharpe_ratio=record.sharpe_ratio,
                    win_rate=record.win_rate,
                    total_trades=record.total_trades,
                )
                for record in records
            ]
        finally:
            db.close()
    
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
        
        result = BacktestResult(
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
        self._save_result(result)
        return result

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
