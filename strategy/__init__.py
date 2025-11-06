"""
策略模块
提供各种交易策略实现
"""

from .base_strategy import BaseStrategy
from .ma_cross_strategy import MACrossStrategy

__all__ = [
    'BaseStrategy',
    'MACrossStrategy',
]
