from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import MarketBase


class Ohlcv(MarketBase):
    __tablename__ = "ohlcv"
    __table_args__ = (
        UniqueConstraint("market", "symbol", "interval", "open_time", name="uq_ohlcv_bar"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    market: Mapped[str] = mapped_column(String(32), index=True)
    symbol: Mapped[str] = mapped_column(String(40), index=True)
    interval: Mapped[str] = mapped_column(String(16), index=True)
    open_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    open: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    high: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    low: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    close: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    volume: Mapped[Decimal] = mapped_column(Numeric(24, 10))

