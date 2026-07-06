from typing import Any, List

from app.modules.indicators.indicators import (
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_momentum,
    calculate_roc,
    calculate_rsi,
    calculate_sma,
    calculate_volume_ma,
)
from app.modules.indicators.schemas import (
    AvailableIndicatorsResponse,
    BollingerBandsResponse,
    EMAResponse,
    IndicatorValue,
    MACDResponse,
    MomentumResponse,
    ROCResponse,
    RSIResponse,
    SMAResponse,
    VolumeMAResponse,
)
from app.modules.market.repository import OhlcvRepository


class IndicatorService:
    def __init__(self):
        self.ohlcv_repository = OhlcvRepository()
    
    def _get_prices_and_timestamps(self, market: str, symbol: str, interval: str, limit: int = 200) -> tuple:
        bars = self.ohlcv_repository.get_ohlcv(market, symbol, interval, limit=limit)
        timestamps = [bar.open_time.isoformat() for bar in bars]
        prices = [float(bar.close) for bar in bars]
        volumes = [float(bar.volume) for bar in bars]
        return timestamps, prices, volumes
    
    def _create_indicator_values(self, timestamps: List[str], values: List) -> List[IndicatorValue]:
        return [
            IndicatorValue(timestamp=timestamps[i], value=values[i])
            for i in range(len(timestamps))
        ]
    
    def calculate_sma(self, market: str, symbol: str, interval: str, period: int = 20) -> SMAResponse:
        timestamps, prices, _ = self._get_prices_and_timestamps(market, symbol, interval, limit=period + 50)
        sma_values = calculate_sma(prices, period)
        return SMAResponse(
            period=period,
            values=self._create_indicator_values(timestamps, sma_values),
        )
    
    def calculate_ema(self, market: str, symbol: str, interval: str, period: int = 20) -> EMAResponse:
        timestamps, prices, _ = self._get_prices_and_timestamps(market, symbol, interval, limit=period + 50)
        ema_values = calculate_ema(prices, period)
        return EMAResponse(
            period=period,
            values=self._create_indicator_values(timestamps, ema_values),
        )
    
    def calculate_macd(
        self,
        market: str,
        symbol: str,
        interval: str,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> MACDResponse:
        max_period = max(fast_period, slow_period, signal_period)
        timestamps, prices, _ = self._get_prices_and_timestamps(market, symbol, interval, limit=max_period + 100)
        macd_line, signal_line, histogram = calculate_macd(prices, fast_period, slow_period, signal_period)
        return MACDResponse(
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period,
            macd_line=self._create_indicator_values(timestamps, macd_line),
            signal_line=self._create_indicator_values(timestamps, signal_line),
            histogram=self._create_indicator_values(timestamps, histogram),
        )
    
    def calculate_rsi(self, market: str, symbol: str, interval: str, period: int = 14) -> RSIResponse:
        timestamps, prices, _ = self._get_prices_and_timestamps(market, symbol, interval, limit=period + 100)
        rsi_values = calculate_rsi(prices, period)
        return RSIResponse(
            period=period,
            values=self._create_indicator_values(timestamps, rsi_values),
        )
    
    def calculate_bollinger_bands(
        self,
        market: str,
        symbol: str,
        interval: str,
        period: int = 20,
        num_std: float = 2.0,
    ) -> BollingerBandsResponse:
        timestamps, prices, _ = self._get_prices_and_timestamps(market, symbol, interval, limit=period + 100)
        upper_band, middle_band, lower_band = calculate_bollinger_bands(prices, period, num_std)
        return BollingerBandsResponse(
            period=period,
            num_std=num_std,
            upper_band=self._create_indicator_values(timestamps, upper_band),
            middle_band=self._create_indicator_values(timestamps, middle_band),
            lower_band=self._create_indicator_values(timestamps, lower_band),
        )
    
    def calculate_momentum(self, market: str, symbol: str, interval: str, period: int = 10) -> MomentumResponse:
        timestamps, prices, _ = self._get_prices_and_timestamps(market, symbol, interval, limit=period + 50)
        momentum_values = calculate_momentum(prices, period)
        return MomentumResponse(
            period=period,
            values=self._create_indicator_values(timestamps, momentum_values),
        )
    
    def calculate_roc(self, market: str, symbol: str, interval: str, period: int = 12) -> ROCResponse:
        timestamps, prices, _ = self._get_prices_and_timestamps(market, symbol, interval, limit=period + 50)
        roc_values = calculate_roc(prices, period)
        return ROCResponse(
            period=period,
            values=self._create_indicator_values(timestamps, roc_values),
        )
    
    def calculate_volume_ma(self, market: str, symbol: str, interval: str, period: int = 20) -> VolumeMAResponse:
        timestamps, _, volumes = self._get_prices_and_timestamps(market, symbol, interval, limit=period + 50)
        volume_ma_values = calculate_volume_ma(volumes, period)
        return VolumeMAResponse(
            period=period,
            values=self._create_indicator_values(timestamps, volume_ma_values),
        )
    
    def get_available_indicators(self) -> AvailableIndicatorsResponse:
        indicators = [
            {
                "name": "SMA",
                "description": "Simple Moving Average",
                "default_period": 20,
                "parameters": ["period"],
            },
            {
                "name": "EMA",
                "description": "Exponential Moving Average",
                "default_period": 20,
                "parameters": ["period"],
            },
            {
                "name": "MACD",
                "description": "Moving Average Convergence Divergence",
                "default_fast_period": 12,
                "default_slow_period": 26,
                "default_signal_period": 9,
                "parameters": ["fast_period", "slow_period", "signal_period"],
            },
            {
                "name": "RSI",
                "description": "Relative Strength Index",
                "default_period": 14,
                "parameters": ["period"],
            },
            {
                "name": "BB",
                "description": "Bollinger Bands",
                "default_period": 20,
                "default_num_std": 2.0,
                "parameters": ["period", "num_std"],
            },
            {
                "name": "MOM",
                "description": "Momentum",
                "default_period": 10,
                "parameters": ["period"],
            },
            {
                "name": "ROC",
                "description": "Rate of Change",
                "default_period": 12,
                "parameters": ["period"],
            },
            {
                "name": "VOLUME_MA",
                "description": "Volume Moving Average",
                "default_period": 20,
                "parameters": ["period"],
            },
        ]
        return AvailableIndicatorsResponse(indicators=indicators)
    
    def calculate_indicator(
        self,
        market: str,
        symbol: str,
        interval: str,
        indicator: str,
        **kwargs,
    ) -> Any:
        indicator_lower = indicator.lower()
        period = kwargs.get("period", 20)
        
        if indicator_lower == "sma":
            return self.calculate_sma(market, symbol, interval, period)
        elif indicator_lower == "ema":
            return self.calculate_ema(market, symbol, interval, period)
        elif indicator_lower == "macd":
            return self.calculate_macd(
                market, symbol, interval,
                kwargs.get("fast_period", 12),
                kwargs.get("slow_period", 26),
                kwargs.get("signal_period", 9),
            )
        elif indicator_lower == "rsi":
            return self.calculate_rsi(market, symbol, interval, kwargs.get("period", 14))
        elif indicator_lower == "bb":
            return self.calculate_bollinger_bands(
                market, symbol, interval,
                period,
                kwargs.get("num_std", 2.0),
            )
        elif indicator_lower == "mom":
            return self.calculate_momentum(market, symbol, interval, period)
        elif indicator_lower == "roc":
            return self.calculate_roc(market, symbol, interval, kwargs.get("period", 12))
        elif indicator_lower == "volume_ma":
            return self.calculate_volume_ma(market, symbol, interval, period)
        else:
            raise ValueError(f"Unknown indicator: {indicator}")


indicator_service = IndicatorService()
