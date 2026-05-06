"""Agent-owned data contracts.

These dataclasses avoid coupling the agent package to FastAPI or Pydantic so
the same package can run as a CLI, SDK, API service, or embedded component.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4


def utc_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def new_id(prefix: str) -> str:
    return f"{prefix}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"


class RunEnv(str, Enum):
    LIVE = "live"
    PAPER = "paper"
    BACKTEST = "backtest"


class AssetClass(str, Enum):
    CRYPTO = "crypto"
    STOCK = "stock"
    FUTURES = "futures"
    COMMODITY = "commodity"
    FOREX = "forex"
    OTHER = "other"


class AgentAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    REDUCE = "REDUCE"
    CLOSE = "CLOSE"
    OBSERVE = "OBSERVE"


class DecisionStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    MODIFIED = "modified"
    EXECUTED = "executed"
    EXPIRED = "expired"


@dataclass
class AssetRef:
    symbol: str
    asset_class: str = AssetClass.CRYPTO.value
    exchange: str = "unknown"
    currency: str = "USDT"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentContext:
    request_id: str = field(default_factory=lambda: new_id("req"))
    run_env: str = RunEnv.PAPER.value
    agent_id: str = "default_agent"
    portfolio_id: str = "default_portfolio"
    account_id: str = "default_account"
    position_group_id: str = "default_group"
    strategy_id: str = "agent_discretionary_v1"
    asset: AssetRef = field(default_factory=lambda: AssetRef(symbol="BTC/USDT"))
    task_type: str = "decision"
    market_context: Dict[str, Any] = field(default_factory=dict)
    portfolio_context: Dict[str, Any] = field(default_factory=dict)
    risk_context: Dict[str, Any] = field(default_factory=dict)
    memory_context: Dict[str, Any] = field(default_factory=dict)
    user_instruction: str = "只给建议，不自动下单"
    created_at: int = field(default_factory=utc_ts)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["asset"] = self.asset.to_dict()
        return data


@dataclass
class AgentDecision:
    decision_id: str
    request_id: str
    run_env: str
    agent_id: str
    portfolio_id: str
    account_id: str
    position_group_id: str
    strategy_id: str
    symbol: str
    asset_class: str
    exchange: str
    action: str
    confidence: float
    reasoning: str
    risk_notes: str
    suggested_price: Optional[float] = None
    suggested_quantity: Optional[float] = None
    timeframe: str = "1h"
    stop_loss: Dict[str, Any] = field(default_factory=dict)
    take_profit: Dict[str, Any] = field(default_factory=dict)
    requires_human_confirmation: bool = True
    status: str = DecisionStatus.PENDING.value
    market_snapshot: Dict[str, Any] = field(default_factory=dict)
    portfolio_snapshot: Dict[str, Any] = field(default_factory=dict)
    risk_snapshot: Dict[str, Any] = field(default_factory=dict)
    memory_snapshot: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: int = field(default_factory=utc_ts)
    updated_at: int = field(default_factory=utc_ts)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentFeedback:
    feedback_id: str
    decision_id: str
    feedback_type: str
    comment: str = ""
    executed_price: Optional[float] = None
    executed_quantity: Optional[float] = None
    result_snapshot: Dict[str, Any] = field(default_factory=dict)
    created_at: int = field(default_factory=utc_ts)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentTradeRecord:
    trade_id: str
    run_env: str
    portfolio_id: str
    account_id: str
    position_group_id: str
    strategy_id: str
    decision_id: Optional[str]
    symbol: str
    asset_class: str
    side: str
    price: float
    quantity: float
    status: str = "recorded"
    source_type: str = "agent"
    realized_pnl: float = 0.0
    fees: float = 0.0
    notes: str = ""
    traded_at: int = field(default_factory=utc_ts)
    created_at: int = field(default_factory=utc_ts)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentPosition:
    position_id: str
    run_env: str
    portfolio_id: str
    account_id: str
    position_group_id: str
    strategy_id: str
    symbol: str
    asset_class: str
    side: str
    entry_price: float
    quantity: float
    status: str = "open"
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    max_drawdown: float = 0.0
    opened_at: int = field(default_factory=utc_ts)
    closed_at: Optional[int] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

