from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field


class AlertType(str, Enum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PRICE_CHANGE = "price_change"
    SIGNAL_ALERT = "signal_alert"
    RISK_ALERT = "risk_alert"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertRule(BaseModel):
    id: Optional[str] = Field(None, description="Alert rule ID")
    name: str = Field(description="Alert rule name")
    type: AlertType = Field(description="Alert type")
    market: str = Field(description="Market type")
    symbol: str = Field(description="Trading symbol")
    threshold: float = Field(description="Alert threshold value")
    severity: AlertSeverity = Field(AlertSeverity.INFO, description="Alert severity")
    enabled: bool = Field(True, description="Whether the alert is enabled")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")


class AlertNotification(BaseModel):
    id: str = Field(description="Notification ID")
    rule_id: str = Field(description="Associated alert rule ID")
    type: AlertType = Field(description="Alert type")
    severity: AlertSeverity = Field(description="Alert severity")
    message: str = Field(description="Alert message")
    market: str = Field(description="Market type")
    symbol: str = Field(description="Trading symbol")
    current_value: float = Field(description="Current value that triggered alert")
    threshold: float = Field(description="Alert threshold")
    timestamp: datetime = Field(description="Alert timestamp")
    read: bool = Field(False, description="Whether the alert has been read")


class PriceAlertRequest(BaseModel):
    name: str = Field(description="Alert name")
    market: str = Field(description="Market type")
    symbol: str = Field(description="Trading symbol")
    type: AlertType = Field(description="Alert type")
    threshold: float = Field(description="Alert threshold")
    severity: Optional[AlertSeverity] = Field(AlertSeverity.INFO, description="Alert severity")


class PriceUpdate(BaseModel):
    market: str = Field(description="Market type")
    symbol: str = Field(description="Trading symbol")
    price: float = Field(description="Current price")
    timestamp: datetime = Field(description="Price timestamp")
    change_24h: Optional[float] = Field(None, description="24h price change percentage")


class SignalAlertRequest(BaseModel):
    strategy_name: str = Field(description="Strategy name")
    market: str = Field(description="Market type")
    symbol: str = Field(description="Trading symbol")
    interval: str = Field(description="Time interval")
    signal_types: Optional[list[str]] = Field(["buy", "sell"], description="Signal types to alert on")


class AlertListResponse(BaseModel):
    alerts: list[AlertNotification] = Field(description="List of alerts")


class AlertRuleListResponse(BaseModel):
    rules: list[AlertRule] = Field(description="List of alert rules")
