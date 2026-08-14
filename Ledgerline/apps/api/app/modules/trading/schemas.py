from datetime import datetime

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    portfolio_id: int = Field(description="Portfolio ID")
    market: str = Field(description="Market type (e.g., crypto, stock, future)")
    symbol: str = Field(description="Trading symbol (e.g., BTCUSDT)")
    side: str = Field(description="Position side (buy/sell)")
    type: str = Field(description="Transaction type (open/add/reduce/close)")
    price: float = Field(description="Execution price")
    quantity: float = Field(description="Quantity traded")
    fee: float = Field(default=0, description="Transaction fee")
    executed_at: datetime | None = Field(default=None, description="Execution timestamp")
    note: str | None = Field(default=None, description="Optional note")


class TransactionResponse(BaseModel):
    id: int
    portfolio_id: int | None
    position_id: int | None
    market: str
    symbol: str
    side: str
    type: str
    quantity: float
    price: float
    amount: float
    fee: float
    created_at: str


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
    total_amount: float
    total_fee: float
    current_price: float | None = None
    pnl: float | None = None
    pnl_percent: float | None = None


class PortfolioSummaryResponse(BaseModel):
    portfolio_id: int
    portfolio_name: str
    total_value: float
    total_pnl: float
    total_pnl_percent: float
    positions: list[PositionSummary]


class PositionDetailResponse(PositionSummary):
    transactions: list[dict] = []


class PortfolioCreate(BaseModel):
    workspace_id: int = Field(description="Workspace ID")
    name: str = Field(description="Portfolio name")
    currency: str = Field(default="USD", description="Base currency (USD/CNY)")


class PortfolioResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    currency: str
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