"""
数据模块
提供数据获取、存储和管理功能
"""

from .models import (
    KlineData, Signal, TradeRecord, Position, AIAnalysis, BacktestResult,
    SignalType, OrderSide, OrderStatus, StopLossType
)
from .db_manager import db_manager, DatabaseManager

__all__ = [
    'KlineData',
    'Signal',
    'TradeRecord',
    'Position',
    'AIAnalysis',
    'BacktestResult',
    'SignalType',
    'OrderSide',
    'OrderStatus',
    'StopLossType',
    'db_manager',
    'DatabaseManager'
]
