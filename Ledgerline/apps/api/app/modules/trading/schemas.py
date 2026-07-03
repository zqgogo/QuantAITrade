from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    portfolio_id: int = Field(description="Portfolio ID")
    market: str = Field(description="Market type (e.g., crypto, stock, future)")
    symbol: str = Field(description="Trading symbol (e.g., BTCUSDT)")
    side: str = Field(description="Position side (long/short)")
    type: str = Field(description="Transaction type (open/add/reduce/close)")
    price: float = Field(description="Execution price")
    quantity: float = Field(description="Quantity traded")
    executed_at: datetime = Field(description="Execution timestamp")
    note: str | None = Field(default=None, description="Optional note")


class TransactionResponse(BaseModel):
    transaction_id: int
    position_id: int
    position_status: str


class PositionSummary(BaseModel):
    position_id: int
    portfolio_id: int
    market: str
    symbol: str
    side: str
    status: str
    opened_at: str | None
    closed_at: str | None
    total_quantity: float
    avg_price: float
    current_price: float | None = None
    pnl: float | None = None
    pnl_pct: float | None = None


class PortfolioSummaryResponse(BaseModel):
    portfolio_id: int
    open_positions_count: int
    total_value_at_avg_price: float
    positions: list[PositionSummary]


class PositionDetailResponse(PositionSummary):
    transactions: list[dict] = []


class PortfolioCreate(BaseModel):
    workspace_id: int = Field(description="Workspace ID")
    name: str = Field(description="Portfolio name")


class PortfolioResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    created_at: str


class WorkspaceCreate(BaseModel):
    name: str = Field(description="Workspace name")


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    created_at: str


class WatchlistCreate(BaseModel):
    portfolio_id: int
    market: str
    symbol: str
    alert_price_high: float | None = None
    alert_price_low: float | None = None
    enabled: bool = True


class WatchlistUpdate(BaseModel):
    alert_price_high: float | None = None
    alert_price_low: float | None = None
    enabled: bool | None = None


class WatchlistResponse(BaseModel):
    id: int
    portfolio_id: int
    market: str
    symbol: str
    alert_price_high: float | None
    alert_price_low: float | None
    enabled: bool
    created_at: str


class NotificationResponse(BaseModel):
    id: int
    portfolio_id: int
    type: str
    status: str
    title: str
    message: str
    symbol: str | None
    created_at: str