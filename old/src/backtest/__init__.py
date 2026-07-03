"""
回测模块
提供策略回测功能
"""

from .engine import BacktestEngine, run_backtest

__all__ = [
    'BacktestEngine',
    'run_backtest',
]
