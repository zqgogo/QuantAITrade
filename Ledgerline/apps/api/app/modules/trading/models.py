from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import TradingBase


class TransactionType(str, Enum):
    OPEN = "open"
    ADD = "add"
    REDUCE = "reduce"
    CLOSE = "close"


class TransactionSide(str, Enum):
    LONG = "long"
    SHORT = "short"


class PositionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class NotificationType(str, Enum):
    PRICE_ALERT = "price_alert"
    SIGNAL_ALERT = "signal_alert"
    NEWS_ALERT = "news_alert"
    REPORT_READY = "report_ready"


class NotificationStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"


class ReportType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Workspace(TradingBase):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    portfolios: Mapped[list["Portfolio"]] = relationship(back_populates="workspace")


class Portfolio(TradingBase):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), index=True)
    name: Mapped[str] = mapped_column(String(80), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    workspace: Mapped[Workspace] = relationship(back_populates="portfolios")
    positions: Mapped[list["Position"]] = relationship(back_populates="portfolio")


class Position(TradingBase):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    market: Mapped[str] = mapped_column(String(32), index=True)
    symbol: Mapped[str] = mapped_column(String(40), index=True)
    side: Mapped[TransactionSide] = mapped_column(String(8))
    status: Mapped[PositionStatus] = mapped_column(String(10), index=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    portfolio: Mapped[Portfolio] = relationship(back_populates="positions")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="position")


class Transaction(TradingBase):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"), index=True)
    type: Mapped[TransactionType] = mapped_column(String(10))
    price: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    executed_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    position: Mapped[Position] = relationship(back_populates="transactions")


class Watchlist(TradingBase):
    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    market: Mapped[str] = mapped_column(String(32), index=True)
    symbol: Mapped[str] = mapped_column(String(40), index=True)
    alert_price_high: Mapped[Decimal | None] = mapped_column(Numeric(24, 10))
    alert_price_low: Mapped[Decimal | None] = mapped_column(Numeric(24, 10))
    enabled: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("portfolio_id", "market", "symbol", name="uq_watchlist_item"),
    )


class Report(TradingBase):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    type: Mapped[ReportType] = mapped_column(String(10), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    period_start: Mapped[datetime] = mapped_column(DateTime)
    period_end: Mapped[datetime] = mapped_column(DateTime)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Notification(TradingBase):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    type: Mapped[NotificationType] = mapped_column(String(20), index=True)
    status: Mapped[NotificationStatus] = mapped_column(String(10), index=True, default=NotificationStatus.UNREAD)
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    symbol: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Note(TradingBase):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    position_id: Mapped[int | None] = mapped_column(ForeignKey("positions.id"), index=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)