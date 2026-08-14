from typing import Any, Dict, List, Optional

from app.modules.market.repository import OhlcvRepository
from app.modules.strategies.schemas import (
    AvailableStrategiesResponse,
    MultiStrategyRunResponse,
    StrategyInfo,
    StrategyRunResponse,
)
from app.modules.strategies.strategies import StrategyRegistry


class StrategyService:
    def __init__(self):
        self.ohlcv_repository = OhlcvRepository()
    
    def _get_prices_and_volumes(self, market: str, symbol: str, interval: str, limit: int = 250) -> tuple:
        bars = self.ohlcv_repository.get_ohlcv(market, symbol, interval, limit=limit)
        prices = [float(bar.close) for bar in bars]
        volumes = [float(bar.volume) for bar in bars]
        return prices, volumes
    
    def run_strategy(
        self,
        market: str,
        symbol: str,
        interval: str,
        strategy_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> StrategyRunResponse:
        strategy = StrategyRegistry.get_strategy(strategy_name)
        
        if not strategy:
            return StrategyRunResponse(
                success=False,
                message=f"Strategy '{strategy_name}' not found",
            )
        
        params = {**strategy.default_parameters, **(parameters or {})}
        params.update({
            "symbol": symbol,
            "market": market,
            "interval": interval,
        })
        
        max_period = self._get_max_period(strategy, params)
        prices, volumes = self._get_prices_and_volumes(market, symbol, interval, limit=max_period + 50)
        
        if len(prices) < max_period:
            return StrategyRunResponse(
                success=False,
                message=f"Insufficient data. Need at least {max_period} bars, got {len(prices)}",
            )
        
        signal = strategy.run(prices, volumes, **params)
        
        return StrategyRunResponse(
            success=True,
            signal=signal,
            message=f"Strategy '{strategy_name}' executed successfully",
        )
    
    def run_multiple_strategies(
        self,
        market: str,
        symbol: str,
        interval: str,
        strategy_names: List[str],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> MultiStrategyRunResponse:
        signals = []
        
        for strategy_name in strategy_names:
            result = self.run_strategy(market, symbol, interval, strategy_name, parameters)
            if result.success and result.signal:
                signals.append(result.signal)
        
        buy_count = sum(1 for s in signals if s.signal_type == "buy")
        sell_count = sum(1 for s in signals if s.signal_type == "sell")
        hold_count = sum(1 for s in signals if s.signal_type == "hold")
        
        if buy_count > sell_count and buy_count > hold_count:
            consensus = "buy"
        elif sell_count > buy_count and sell_count > hold_count:
            consensus = "sell"
        else:
            consensus = "hold"
        
        avg_confidence = sum(s.confidence for s in signals) / len(signals) if signals else 0
        
        summary = {
            "total_strategies": len(strategy_names),
            "successful_strategies": len(signals),
            "buy_signals": buy_count,
            "sell_signals": sell_count,
            "hold_signals": hold_count,
            "consensus": consensus,
            "average_confidence": avg_confidence,
        }
        
        return MultiStrategyRunResponse(
            signals=signals,
            summary=summary,
        )
    
    def get_available_strategies(self) -> AvailableStrategiesResponse:
        strategies = StrategyRegistry.get_all_strategies()
        strategy_infos = []
        
        for strategy in strategies:
            strategy_infos.append(StrategyInfo(
                name=strategy.name,
                description=strategy.description,
                parameters=strategy.parameters,
                default_parameters=strategy.default_parameters,
            ))
        
        return AvailableStrategiesResponse(strategies=strategy_infos)
    
    def _get_max_period(self, strategy, parameters: Dict[str, Any]) -> int:
        periods = []
        
        if strategy.name == "rsi":
            periods.append(parameters.get("period", 14))
        elif strategy.name == "macd":
            periods.append(parameters.get("fast_period", 12))
            periods.append(parameters.get("slow_period", 26))
            periods.append(parameters.get("signal_period", 9))
        elif strategy.name == "ma_cross":
            periods.append(parameters.get("short_period", 50))
            periods.append(parameters.get("long_period", 200))
        elif strategy.name == "bollinger":
            periods.append(parameters.get("period", 20))
        
        return max(periods) if periods else 200


strategy_service = StrategyService()
