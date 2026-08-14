from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import TradingBase


class AlertRuleRecord(TradingBase):
    __tablename__ = "alert_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(20))
    market: Mapped[str] = mapped_column(String(20))
    symbol: Mapped[str] = mapped_column(String(50))
    threshold: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String(20))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class AlertNotificationRecord(TradingBase):
    __tablename__ = "alert_notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(36))
    type: Mapped[str] = mapped_column(String(20))
    severity: Mapped[str] = mapped_column(String(20))
    message: Mapped[str] = mapped_column(String(500))
    market: Mapped[str] = mapped_column(String(20))
    symbol: Mapped[str] = mapped_column(String(50))
    current_value: Mapped[float] = mapped_column(Float)
    threshold: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime)
    read: Mapped[bool] = mapped_column(Boolean, default=False)