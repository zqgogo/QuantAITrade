from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import ccxt


class OhlcvBar:
    def __init__(self, open_time: datetime, open: float, high: float, low: float, close: float, volume: float):
        self.open_time = open_time
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume


class ExchangeConnector(ABC):
    @abstractmethod
    def fetch_ohlcv(
        self,
        symbol: str,
        interval: str,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[OhlcvBar]:
        pass

    @abstractmethod
    def get_current_price(self, symbol: str) -> float:
        pass

    @abstractmethod
    def get_exchange_info(self) -> Dict[str, Any]:
        pass


class CcxtConnector(ExchangeConnector):
    def __init__(self, exchange_name: str = "binance", config: Optional[Dict[str, Any]] = None):
        self.exchange_name = exchange_name
        self.config = config or {}
        self._exchange = self._create_exchange()

    def _create_exchange(self) -> ccxt.Exchange:
        exchange_class = getattr(ccxt, self.exchange_name)
        default_config = {
            "enableRateLimit": True,
            "options": {
                "defaultType": "spot",
            },
        }
        default_config.update(self.config)
        return exchange_class(default_config)

    def fetch_ohlcv(
        self,
        symbol: str,
        interval: str,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[OhlcvBar]:
        since_timestamp = int(since.timestamp() * 1000) if since else None
        ohlcv_data = self._exchange.fetch_ohlcv(symbol, interval, since=since_timestamp, limit=limit)
        
        bars = []
        for bar in ohlcv_data:
            open_time = datetime.fromtimestamp(bar[0] / 1000)
            bars.append(OhlcvBar(
                open_time=open_time,
                open=float(bar[1]),
                high=float(bar[2]),
                low=float(bar[3]),
                close=float(bar[4]),
                volume=float(bar[5]),
            ))
        return bars

    def get_current_price(self, symbol: str) -> float:
        ticker = self._exchange.fetch_ticker(symbol)
        return float(ticker["last"])

    def get_exchange_info(self) -> Dict[str, Any]:
        return {
            "name": self._exchange.name,
            "id": self._exchange.id,
            "symbols": self._exchange.symbols,
            "timeframes": list(self._exchange.timeframes.keys()),
        }


class MockConnector(ExchangeConnector):
    def __init__(self):
        pass

    def fetch_ohlcv(
        self,
        symbol: str,
        interval: str,
        since: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[OhlcvBar]:
        bars = []
        current_time = datetime.now()
        limit = limit or 100
        
        for i in range(limit):
            base_price = 60000.0 if "BTC" in symbol else 3000.0
            open_time = current_time - timedelta(minutes=(limit - i) * self._interval_minutes(interval))
            bars.append(OhlcvBar(
                open_time=open_time,
                open=base_price + (i % 10) * 100,
                high=base_price + (i % 10) * 100 + 50,
                low=base_price + (i % 10) * 100 - 50,
                close=base_price + ((i + 1) % 10) * 100,
                volume=10.0 + i * 0.5,
            ))
        return bars

    def get_current_price(self, symbol: str) -> float:
        return 60000.0 if "BTC" in symbol else 3000.0

    def get_exchange_info(self) -> Dict[str, Any]:
        return {
            "name": "Mock Exchange",
            "id": "mock",
            "symbols": ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
            "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
        }

    @staticmethod
    def _interval_minutes(interval: str) -> int:
        mapping = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "1h": 60,
            "4h": 240,
            "1d": 1440,
        }
        return mapping.get(interval, 60)


def create_connector(exchange_name: str = "binance", use_mock: bool = False) -> ExchangeConnector:
    if use_mock:
        return MockConnector()
    return CcxtConnector(exchange_name)
