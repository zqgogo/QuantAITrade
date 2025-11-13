"""
数据模型定义
定义系统使用的数据结构
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class SignalType(Enum):
    """信号类型枚举"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class OrderSide(Enum):
    """订单方向枚举"""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """订单状态枚举"""
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    PENDING_CANCEL = "PENDING_CANCEL"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    PENDING = "PENDING"  # 添加缺失的PENDING状态


class OrderType(Enum):
    """订单类型枚举"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_MARKET = "STOP_MARKET"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_MARKET = "TAKE_PROFIT_MARKET"
    TRAILING_STOP = "TRAILING_STOP"


class StopLossType(Enum):
    """止损类型枚举"""
    FIXED_PERCENT = "fixed_percent"       # 固定百分比
    KEY_LEVEL = "key_level"               # 关键点位
    ATR_BASED = "atr_based"               # ATR动态
    TRAILING = "trailing"                 # 移动止损
    TIME_BASED = "time_based"             # 时间止损
    MANUAL = "manual"                     # 手动指定


@dataclass
class KlineData:
    """K线数据模型"""
    symbol: str
    interval: str
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int
    quote_volume: float = 0.0
    trades_count: int = 0
    created_at: int = field(default_factory=lambda: int(datetime.now().timestamp()))


@dataclass
class Signal:
    """交易信号模型"""
    strategy_name: str
    symbol: str
    signal_type: SignalType
    price: float
    confidence: float
    reason: str = ""
    timestamp: int = field(default_factory=lambda: int(datetime.now().timestamp()))
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'strategy_name': self.strategy_name,
            'symbol': self.symbol,
            'signal_type': self.signal_type.value,
            'price': self.price,
            'confidence': self.confidence,
            'reason': self.reason,
            'timestamp': self.timestamp,
            'parameters': self.parameters
        }


@dataclass
class TradeRecord:
    """交易记录模型"""
    symbol: str
    side: OrderSide
    price: float
    quantity: float
    strategy_name: str
    order_type: str = "MARKET"
    status: OrderStatus = OrderStatus.PENDING
    order_id: Optional[str] = None
    stop_loss_price: Optional[float] = None
    stop_loss_type: Optional[StopLossType] = None
    timestamp: int = field(default_factory=lambda: int(datetime.now().timestamp()))
    pnl: float = 0.0
    pnl_percent: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'side': self.side.value,
            'price': self.price,
            'quantity': self.quantity,
            'strategy_name': self.strategy_name,
            'order_type': self.order_type,
            'status': self.status.value,
            'order_id': self.order_id,
            'stop_loss_price': self.stop_loss_price,
            'stop_loss_type': self.stop_loss_type.value if self.stop_loss_type else None,
            'timestamp': self.timestamp,
            'pnl': self.pnl,
            'pnl_percent': self.pnl_percent
        }


@dataclass
class Position:
    """持仓模型"""
    symbol: str
    entry_price: float
    quantity: float
    strategy_name: str
    stop_loss_type: StopLossType
    stop_loss_price: float
    initial_stop_price: float
    highest_price: float
    entry_time: int = field(default_factory=lambda: int(datetime.now().timestamp()))
    unrealized_pnl: float = 0.0
    unrealized_pnl_percent: float = 0.0


@dataclass
class AIAnalysis:
    """AI分析结果模型"""
    analysis_date: str
    market_summary: str
    suggestions: Dict[str, Any]
    risk_alert: str
    model_version: str
    created_at: int = field(default_factory=lambda: int(datetime.now().timestamp()))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'analysis_date': self.analysis_date,
            'market_summary': self.market_summary,
            'suggestions': self.suggestions,
            'risk_alert': self.risk_alert,
            'model_version': self.model_version,
            'created_at': self.created_at
        }


@dataclass
class BacktestResult:
    """回测结果模型"""
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    parameters: Dict[str, Any]
    created_at: int = field(default_factory=lambda: int(datetime.now().timestamp()))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'strategy_name': self.strategy_name,
            'symbol': self.symbol,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'initial_capital': self.initial_capital,
            'final_capital': self.final_capital,
            'total_return': self.total_return,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'parameters': self.parameters,
            'created_at': self.created_at
        }


@dataclass
class Order:
    """订单模型"""
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None  # 限价单价格
    order_id: Optional[str] = None  # 交易所订单ID
    client_order_id: Optional[str] = None  # 客户端订单ID
    executed_qty: float = 0.0  # 已成交数量
    status: OrderStatus = OrderStatus.NEW
    created_time: int = field(default_factory=lambda: int(datetime.now().timestamp()))
    updated_time: int = field(default_factory=lambda: int(datetime.now().timestamp()))
    strategy_name: str = "Unknown"  # 添加策略名称字段
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'side': self.side.value,
            'order_type': self.order_type.value,
            'quantity': self.quantity,
            'price': self.price,
            'order_id': self.order_id,
            'client_order_id': self.client_order_id,
            'executed_qty': self.executed_qty,
            'status': self.status.value,
            'created_time': self.created_time,
            'updated_time': self.updated_time,
            'strategy_name': self.strategy_name
        }
