from datetime import datetime
from typing import List, Optional

from app.modules.market.exchange_connector import OhlcvBar, create_connector
from app.modules.market.repository import OhlcvRepository
from app.modules.market.schemas import (
    DataProgressResponse,
    OhlcvBarResponse,
    OhlcvResponse,
    PriceResponse,
    RefreshResponse,
)


class MarketService:
    def __init__(self, exchange_name: str = "binance", use_mock: bool = False):
        self.connector = create_connector(exchange_name, use_mock)
        self.repository = OhlcvRepository()

    def get_ohlcv(
        self,
        market: str,
        symbol: str,
        interval: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = 100,
    ) -> OhlcvResponse:
        bars = self.repository.get_ohlcv(
            market=market,
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        
        bar_responses = [
            OhlcvBarResponse(
                open_time=bar.open_time,
                open=float(bar.open),
                high=float(bar.high),
                low=float(bar.low),
                close=float(bar.close),
                volume=float(bar.volume),
            )
            for bar in bars
        ]
        
        return OhlcvResponse(
            market=market,
            symbol=symbol,
            interval=interval,
            bars=bar_responses,
        )

    def refresh_ohlcv(
        self,
        market: str,
        symbol: str,
        interval: str,
        limit: int = 100,
    ) -> RefreshResponse:
        latest_bar = self.repository.get_latest_bar(market, symbol, interval)
        since_time = latest_bar.open_time if latest_bar else None
        
        try:
            fetched_bars = self.connector.fetch_ohlcv(
                symbol=symbol,
                interval=interval,
                since=since_time,
                limit=limit,
            )
        except Exception as e:
            return RefreshResponse(
                success=False,
                message=f"Failed to fetch data: {str(e)}",
                fetched_count=0,
                inserted_count=0,
            )
        
        if not fetched_bars:
            return RefreshResponse(
                success=True,
                message="No new data to fetch",
                fetched_count=0,
                inserted_count=0,
            )
        
        bars_to_insert = []
        for bar in fetched_bars:
            if since_time and bar.open_time <= since_time:
                continue
            bars_to_insert.append({
                "market": market,
                "symbol": symbol,
                "interval": interval,
                "open_time": bar.open_time,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            })
        
        inserted_count = self.repository.bulk_insert(bars_to_insert)
        
        return RefreshResponse(
            success=True,
            message=f"Successfully refreshed {symbol} {interval}",
            fetched_count=len(fetched_bars),
            inserted_count=inserted_count,
        )

    def get_current_price(self, market: str, symbol: str) -> PriceResponse:
        try:
            price = self.connector.get_current_price(symbol)
            return PriceResponse(
                market=market,
                symbol=symbol,
                price=price,
                timestamp=datetime.now(),
            )
        except Exception as e:
            raise Exception(f"Failed to get price: {str(e)}")

    def get_data_progress(self, market: str, symbol: str, interval: str) -> DataProgressResponse:
        latest_bar = self.repository.get_latest_bar(market, symbol, interval)
        earliest_bar = self.repository.get_earliest_bar(market, symbol, interval)
        total_bars = self.repository.get_bar_count(market, symbol, interval)
        
        return DataProgressResponse(
            market=market,
            symbol=symbol,
            interval=interval,
            last_fetch_time=datetime.now() if latest_bar else None,
            total_bars=total_bars,
            earliest_time=earliest_bar.open_time if earliest_bar else None,
            latest_time=latest_bar.open_time if latest_bar else None,
        )

    def close(self):
        self.repository.close()


market_service = MarketService(use_mock=True)
