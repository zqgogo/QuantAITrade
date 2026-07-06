from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.modules.indicators.indicators import (
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
)
from app.modules.strategies.schemas import Signal


class StrategyBase(ABC):
    name: str = "base"
    description: str = "Base strategy"
    parameters: List[Dict[str, Any]] = []
    default_parameters: Dict[str, Any] = {}

    @abstractmethod
    def run(self, prices: List[float], volumes: Optional[List[float]] = None, **kwargs) -> Signal:
        pass

    def get_signal(
        self,
        signal_type: str,
        strength: float,
        confidence: float,
        symbol: str,
        market: str,
        interval: str,
        message: Optional[str] = None,
        parameters: Optional[dict] = None,
    ) -> Signal:
        return Signal(
            signal_type=signal_type,
            strength=strength,
            confidence=confidence,
            strategy=self.name,
            symbol=symbol,
            market=market,
            interval=interval,
            timestamp=datetime.now(),
            message=message,
            parameters=parameters,
        )


class RSIStrategy(StrategyBase):
    name = "rsi"
    description = "RSI Overbought/Oversold Strategy"
    parameters = [
        {"name": "period", "type": "int", "default": 14, "description": "RSI period"},
        {"name": "oversold_threshold", "type": "float", "default": 30, "description": "Oversold threshold"},
        {"name": "overbought_threshold", "type": "float", "default": 70, "description": "Overbought threshold"},
    ]
    default_parameters = {"period": 14, "oversold_threshold": 30, "overbought_threshold": 70}

    def run(self, prices: List[float], volumes: Optional[List[float]] = None, **kwargs) -> Signal:
        period = kwargs.get("period", 14)
        oversold_threshold = kwargs.get("oversold_threshold", 30)
        overbought_threshold = kwargs.get("overbought_threshold", 70)

        rsi_values = calculate_rsi(prices, period)
        
        if len(rsi_values) < 2:
            return self.get_signal(
                signal_type="hold",
                strength=0.0,
                confidence=0.0,
                symbol=kwargs.get("symbol", ""),
                market=kwargs.get("market", ""),
                interval=kwargs.get("interval", ""),
                message="Insufficient data",
                parameters=kwargs,
            )

        current_rsi = rsi_values[-1]
        prev_rsi = rsi_values[-2]

        if current_rsi is None or prev_rsi is None:
            return self.get_signal(
                signal_type="hold",
                strength=0.0,
                confidence=0.0,
                symbol=kwargs.get("symbol", ""),
                market=kwargs.get("market", ""),
                interval=kwargs.get("interval", ""),
                message="Insufficient data",
                parameters=kwargs,
            )

        if current_rsi <= oversold_threshold and prev_rsi > oversold_threshold:
            strength = min((oversold_threshold - current_rsi) / oversold_threshold, 1.0)
            return self.get_signal(
                signal_type="buy",
                strength=strength,
                confidence=0.7 + strength * 0.3,
                symbol=kwargs.get("symbol", ""),
                market=kwargs.get("market", ""),
                interval=kwargs.get("interval", ""),
                message=f"RSI crossed below {oversold_threshold} (oversold)",
                parameters=kwargs,
            )
        elif current_rsi >= overbought_threshold and prev_rsi < overbought_threshold:
            strength = min((current_rsi - overbought_threshold) / (100 - overbought_threshold), 1.0)
            return self.get_signal(
                signal_type="sell",
                strength=strength,
                confidence=0.7 + strength * 0.3,
                symbol=kwargs.get("symbol", ""),
                market=kwargs.get("market", ""),
                interval=kwargs.get("interval", ""),
                message=f"RSI crossed above {overbought_threshold} (overbought)",
                parameters=kwargs,
            )
        else:
            return self.get_signal(
                signal_type="hold",
                strength=0.0,
                confidence=0.5,
                symbol=kwargs.get("symbol", ""),
                market=kwargs.get("market", ""),
                interval=kwargs.get("interval", ""),
                message=f"RSI is {current_rsi:.2f}, no signal",
                parameters=kwargs,
            )


class MACDStrategy(StrategyBase):
    name = "macd"
    description = "MACD Crossover Strategy"
    parameters = [
        {"name": "fast_period", "type": "int", "default": 12, "description": "Fast EMA period"},
        {"name": "slow_period", "type": "int", "default": 26, "description": "Slow EMA period"},
        {"name": "signal_period", "type": "int", "default": 9, "description": "Signal period"},
    ]
    default_parameters = {"fast_period": 12, "slow_period": 26, "signal_period": 9}

    def run(self, prices: List[float], volumes: Optional[List[float]] = None, **kwargs) -> Signal:
        fast_period = kwargs.get("fast_period", 12)
        slow_period = kwargs.get("slow_period", 26)
        signal_period = kwargs.get("signal_period", 9)

        macd_line, signal_line, _ = calculate_macd(prices, fast_period, slow_period, signal_period)

        if len(macd_line) < 2 or len(signal_line) < 2:
            return self.get_signal(
                signal_type="hold",
                strength=0.0,
                confidence=0.0,
                symbol=kwargs.get("symbol", ""),
                market=kwargs.get("market", ""),
                interval=kwargs.get("interval", ""),
                message="Insufficient data",
                parameters=kwargs,
            )

        current_macd = macd_line[-1]
        prev_macd = macd_line[-2]
        current_signal = signal_line[-1]
        prev_signal = signal_line[-2]

        if current_macd is None or prev_macd is None or current_signal is None or prev_signal is None:
            return self.get_signal(
                signal_type="hold",
                strength=0.0,
                confidence=0.0,
                symbol=kwargs.get("symbol", ""),
                market=kwargs.get("market", ""),
                interval=kwargs.get("interval", ""),
                message="Insufficient data",
                parameters=kwargs,
            )

        if prev_macd <= prev_signal and current_macd > current_signal:
            strength = min(current_macd / max(abs(current_macd), 1), 1.0) if current_macd > 0 else 0.5
            return self.get_signal(
                signal_type="buy",
                strength=min(strength, 1.0),
                confidence=0.75,
                symbol=kwargs.get("symbol", ""),
                market=kwargs.get("market", ""),
                interval=kwargs.get("interval", ""),
                message="MACD line crossed above signal line (bullish crossover)",
                parameters=kwargs,
            )
        elif prev_macd >= prev_signal and current_macd < current_signal:
            strength = min(abs(current_macd) / max(abs(current_macd), 1), 1.0) if current_macd < 0 else 0.5
            return self.get_signal(
                signal_type="sell",
                strength=min(strength, 1.0),
                confidence=0.75,
                symbol=kwargs.get("symbol", ""),
                market=kwargs.get("market", ""),
                interval=kwargs.get("interval", ""),
                message="MACD line crossed below signal line (bearish crossover)",
                parameters=kwargs,
            )
        else:
            return self.get_signal(
                signal_type="hold",
                strength=0.0,
                confidence=0.5,
                symbol=kwargs.get("symbol", ""),
                market=kwargs.get("market", ""),
                interval=kwargs.get("interval", ""),
                message="No MACD crossover",
                parameters=kwargs,
            )


class MovingAverageCrossStrategy(StrategyBase):
    name = "ma_cross"
    description = "Moving Average Crossover Strategy"
    parameters = [
        {"name": "short_period", "type": "int", "default": 50, "description": "Short MA period"},
        {"name": "long_period", "type": "int", "default": 200, "description": "Long MA period"},
        {"name": "ma_type", "type": "str", "default": "sma", "description": "MA type: sma or ema"},
    ]
    default_parameters = {"short_period": 50, "long_period": 200, "ma_type": "sma"}

    def run(self, prices: List[float], volumes: Optional[List[float]] = None, **kwargs) -> Signal:
        short_period = kwargs.get("short_period", 50)
        long_period = kwargs.get("long_period", 200)
        ma_type = kwargs.get("ma_type", "sma")

        if ma_type == "ema":
            short_ma = calculate_ema(prices, short_period)
            long_ma = calculate_ema(prices, long_period)
        else:
            short_ma = calculate_sma(prices, short_period)
            long_ma = calculate_sma(prices, long_period)

        if len(short_ma) < 2 or len(long_ma) < 2:
            return self.get_signal(
                signal_type="hold",
                strength=0.0,
                confidence=0.0,
                symbol=kwargs.get("symbol", ""),
                market=kwargs.get("market", ""),
                interval=kwargs.get("interval", ""),
                message="Insufficient data",
                parameters=kwargs,
            )

        current_short = short_ma[-1]
        prev_short = short_ma[-2]
        current_long = long_ma[-1]
        prev_long = long_ma[-2]

        if current_short is None or prev_short is None or current_long is None or prev_long is None:
            return self.get_signal(
                signal_type="hold",
                strength=0.0,
                confidence=0.0,
                symbol=kwargs.get("symbol", ""),
                market=kwargs.get("market", ""),
                interval=kwargs.get("interval", ""),
                message="Insufficient data",
                parameters=kwargs,
            )

        if prev_short <= prev_long and current_short > current_long:
            strength = min((current_short - current_long) / current_long * 100, 1.0) if current_long > 0 else 0.5
            return self.get_signal(
                signal_type="buy",
                strength=min(strength, 1.0),
                confidence=0.8,
                symbol=kwargs.get("symbol", ""),
                market=kwargs.get("market", ""),
                interval=kwargs.get("interval", ""),
                message=f"{ma_type.upper()} {short_period} crossed above {long_period} (golden cross)",
                parameters=kwargs,
            )
        elif prev_short >= prev_long and current_short < current_long:
            strength = min((current_long - current_short) / current_long * 100, 1.0) if current_long > 0 else 0.5
            return self.get_signal(
                signal_type="sell",
                strength=min(strength, 1.0),
                confidence=0.8,
                symbol=kwargs.get("symbol", ""),
                market=kwargs.get("market", ""),
                interval=kwargs.get("interval", ""),
                message=f"{ma_type.upper()} {short_period} crossed below {long_period} (death cross)",
                parameters=kwargs,
            )
        else:
            return self.get_signal(
                signal_type="hold",
                strength=0.0,
                confidence=0.5,
                symbol=kwargs.get("symbol", ""),
                market=kwargs.get("market", ""),
                interval=kwargs.get("interval", ""),
                message="No MA crossover",
                parameters=kwargs,
            )


class BollingerBandsStrategy(StrategyBase):
    name = "bollinger"
    description = "Bollinger Bands Strategy"
    parameters = [
        {"name": "period", "type": "int", "default": 20, "description": "BB period"},
        {"name": "num_std", "type": "float", "default": 2.0, "description": "Number of standard deviations"},
    ]
    default_parameters = {"period": 20, "num_std": 2.0}

    def run(self, prices: List[float], volumes: Optional[List[float]] = None, **kwargs) -> Signal:
        period = kwargs.get("period", 20)
        num_std = kwargs.get("num_std", 2.0)

        upper_band, middle_band, lower_band = calculate_bollinger_bands(prices, period, num_std)

        if len(prices) < 2 or len(upper_band) < 2 or len(lower_band) < 2:
            return self.get_signal(
                signal_type="hold",
                strength=0.0,
                confidence=0.0,
                symbol=kwargs.get("symbol", ""),
                market=kwargs.get("market", ""),
                interval=kwargs.get("interval", ""),
                message="Insufficient data",
                parameters=kwargs,
            )

        current_price = prices[-1]
        prev_price = prices[-2]
        current_upper = upper_band[-1]
        prev_upper = upper_band[-2]
        current_lower = lower_band[-1]
        prev_lower = lower_band[-2]

        if current_upper is None or prev_upper is None or current_lower is None or prev_lower is None:
            return self.get_signal(
                signal_type="hold",
                strength=0.0,
                confidence=0.0,
                symbol=kwargs.get("symbol", ""),
                market=kwargs.get("market", ""),
                interval=kwargs.get("interval", ""),
                message="Insufficient data",
                parameters=kwargs,
            )

        if prev_price >= prev_lower and current_price < current_lower:
            return self.get_signal(
                signal_type="buy",
                strength=0.8,
                confidence=0.7,
                symbol=kwargs.get("symbol", ""),
                market=kwargs.get("market", ""),
                interval=kwargs.get("interval", ""),
                message="Price crossed below lower Bollinger Band (oversold)",
                parameters=kwargs,
            )
        elif prev_price <= prev_upper and current_price > current_upper:
            return self.get_signal(
                signal_type="sell",
                strength=0.8,
                confidence=0.7,
                symbol=kwargs.get("symbol", ""),
                market=kwargs.get("market", ""),
                interval=kwargs.get("interval", ""),
                message="Price crossed above upper Bollinger Band (overbought)",
                parameters=kwargs,
            )
        else:
            return self.get_signal(
                signal_type="hold",
                strength=0.0,
                confidence=0.5,
                symbol=kwargs.get("symbol", ""),
                market=kwargs.get("market", ""),
                interval=kwargs.get("interval", ""),
                message="Price within Bollinger Bands",
                parameters=kwargs,
            )


class StrategyRegistry:
    _strategies: Dict[str, StrategyBase] = {}

    @classmethod
    def register(cls, strategy: StrategyBase):
        cls._strategies[strategy.name] = strategy

    @classmethod
    def get_strategy(cls, name: str) -> Optional[StrategyBase]:
        return cls._strategies.get(name)

    @classmethod
    def get_all_strategies(cls) -> List[StrategyBase]:
        return list(cls._strategies.values())


StrategyRegistry.register(RSIStrategy())
StrategyRegistry.register(MACDStrategy())
StrategyRegistry.register(MovingAverageCrossStrategy())
StrategyRegistry.register(BollingerBandsStrategy())
