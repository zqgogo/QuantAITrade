from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import MarketSessionLocal
from app.modules.market.models import Ohlcv


class OhlcvRepository:
    def __init__(self, db: Optional[Session] = None):
        self.db = db or MarketSessionLocal()

    def get_ohlcv(
        self,
        market: str,
        symbol: str,
        interval: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Ohlcv]:
        query = select(Ohlcv).where(
            Ohlcv.market == market,
            Ohlcv.symbol == symbol,
            Ohlcv.interval == interval,
        )
        
        if start_time:
            query = query.where(Ohlcv.open_time >= start_time)
        if end_time:
            query = query.where(Ohlcv.open_time <= end_time)
        
        query = query.order_by(Ohlcv.open_time)
        
        if limit:
            query = query.limit(limit)
        
        return self.db.execute(query).scalars().all()

    def get_latest_bar(self, market: str, symbol: str, interval: str) -> Optional[Ohlcv]:
        query = select(Ohlcv).where(
            Ohlcv.market == market,
            Ohlcv.symbol == symbol,
            Ohlcv.interval == interval,
        ).order_by(desc(Ohlcv.open_time)).limit(1)
        
        return self.db.execute(query).scalar_one_or_none()

    def get_earliest_bar(self, market: str, symbol: str, interval: str) -> Optional[Ohlcv]:
        query = select(Ohlcv).where(
            Ohlcv.market == market,
            Ohlcv.symbol == symbol,
            Ohlcv.interval == interval,
        ).order_by(Ohlcv.open_time).limit(1)
        
        return self.db.execute(query).scalar_one_or_none()

    def get_bar_count(self, market: str, symbol: str, interval: str) -> int:
        query = select(Ohlcv).where(
            Ohlcv.market == market,
            Ohlcv.symbol == symbol,
            Ohlcv.interval == interval,
        )
        
        return len(self.db.execute(query).scalars().all())

    def bulk_insert(self, bars: List[dict]) -> int:
        inserted_count = 0
        for bar in bars:
            ohlcv = Ohlcv(
                market=bar["market"],
                symbol=bar["symbol"],
                interval=bar["interval"],
                open_time=bar["open_time"],
                open=bar["open"],
                high=bar["high"],
                low=bar["low"],
                close=bar["close"],
                volume=bar["volume"],
            )
            try:
                self.db.add(ohlcv)
                self.db.commit()
                inserted_count += 1
            except IntegrityError:
                self.db.rollback()
        
        return inserted_count

    def close(self):
        if self.db:
            self.db.close()
