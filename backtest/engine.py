"""
回测引擎
基于历史数据验证策略有效性
"""

import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from strategy.base_strategy import BaseStrategy
from data.models import Signal, SignalType, BacktestResult, TradeRecord, OrderSide, OrderStatus
from data.db_manager import db_manager


class BacktestEngine:
    """回测引擎类"""
    
    def __init__(
        self,
        strategy: BaseStrategy,
        initial_capital: float = 10000.0,
        commission_rate: float = 0.001
    ):
        """
        初始化回测引擎
        
        Args:
            strategy: 策略实例
            initial_capital: 初始资金
            commission_rate: 手续费率（默认0.1%）
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        
        # 账户状态
        self.capital = initial_capital
        self.position = 0.0  # 持仓数量
        self.entry_price = 0.0  # 买入价格
        
        # 交易记录
        self.trades: List[TradeRecord] = []
        self.equity_curve: List[float] = []
        
        logger.info(f"回测引擎初始化: 策略={strategy.name}, 初始资金={initial_capital}")
    
    def run(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = '1h'
    ) -> BacktestResult:
        """
        运行回测
        
        Args:
            symbol: 交易对
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            interval: K线周期
            
        Returns:
            回测结果
        """
        logger.info(f"开始回测: {symbol} ({start_date} ~ {end_date})")
        
        # 获取历史数据
        start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
        end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())
        
        klines = db_manager.get_klines(
            symbol=symbol,
            interval=interval,
            start_time=start_ts,
            end_time=end_ts
        )
        
        if not klines:
            logger.error(f"未找到{symbol}的历史数据")
            return None
        
        # 转换为DataFrame
        df = pd.DataFrame(klines)
        df['symbol'] = symbol
        logger.info(f"加载数据: {len(df)}条K线")
        
        # 逐条处理数据
        for i in range(len(df)):
            # 获取当前数据窗口
            window_df = df.iloc[:i+1]
            
            if len(window_df) < self.strategy.get_min_periods():
                continue
            
            # 生成信号
            signal = self.strategy.on_data(window_df)
            
            if signal:
                self._execute_signal(signal, window_df.iloc[-1])
            
            # 记录权益曲线
            current_equity = self._calculate_equity(df.iloc[i]['close'])
            self.equity_curve.append(current_equity)
        
        # 平仓（如果还有持仓）
        if self.position > 0:
            final_price = df.iloc[-1]['close']
            self._close_position(final_price, "回测结束")
        
        # 计算回测结果
        result = self._calculate_results(symbol, start_date, end_date)
        
        logger.success(f"回测完成: 总收益={result.total_return*100:.2f}%, "
                      f"夏普比率={result.sharpe_ratio:.2f}, "
                      f"最大回撤={result.max_drawdown*100:.2f}%")
        
        return result
    
    def _execute_signal(self, signal: Signal, current_bar: pd.Series):
        """
        执行交易信号
        
        Args:
            signal: 交易信号
            current_bar: 当前K线数据
        """
        current_price = float(current_bar['close'])
        
        if signal.signal_type == SignalType.BUY and self.position == 0:
            # 买入
            # 计算可买入数量（扣除手续费）
            available_capital = self.capital * (1 - self.commission_rate)
            quantity = available_capital / current_price
            
            self.position = quantity
            self.entry_price = current_price
            self.capital = 0.0
            
            # 记录交易
            trade = TradeRecord(
                symbol=signal.symbol,
                side=OrderSide.BUY,
                price=current_price,
                quantity=quantity,
                strategy_name=self.strategy.name,
                status=OrderStatus.FILLED,
                timestamp=int(current_bar['open_time'])
            )
            self.trades.append(trade)
            
            logger.debug(f"买入: {quantity:.4f} @ {current_price:.2f}")
            
        elif signal.signal_type == SignalType.SELL and self.position > 0:
            # 卖出
            self._close_position(current_price, "策略信号")
    
    def _close_position(self, price: float, reason: str = ""):
        """
        平仓
        
        Args:
            price: 平仓价格
            reason: 平仓原因
        """
        # 计算收益
        sell_value = self.position * price
        commission = sell_value * self.commission_rate
        self.capital = sell_value - commission
        
        # 计算盈亏
        pnl = self.capital - self.initial_capital
        pnl_percent = pnl / self.initial_capital
        
        # 记录交易
        trade = TradeRecord(
            symbol=self.trades[-1].symbol if self.trades else "UNKNOWN",
            side=OrderSide.SELL,
            price=price,
            quantity=self.position,
            strategy_name=self.strategy.name,
            status=OrderStatus.FILLED,
            pnl=pnl,
            pnl_percent=pnl_percent,
            timestamp=int(datetime.now().timestamp())
        )
        self.trades.append(trade)
        
        logger.debug(f"卖出: {self.position:.4f} @ {price:.2f}, "
                   f"盈亏: {pnl:.2f} ({pnl_percent*100:.2f}%) - {reason}")
        
        self.position = 0.0
        self.entry_price = 0.0
    
    def _calculate_equity(self, current_price: float) -> float:
        """计算当前权益"""
        if self.position > 0:
            return self.position * current_price
        else:
            return self.capital
    
    def _calculate_results(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> BacktestResult:
        """计算回测结果"""
        final_capital = self.capital
        total_return = (final_capital - self.initial_capital) / self.initial_capital
        
        # 计算夏普比率
        if len(self.equity_curve) > 1:
            returns = pd.Series(self.equity_curve).pct_change().dropna()
            sharpe_ratio = returns.mean() / returns.std() * (252 ** 0.5) if returns.std() > 0 else 0
        else:
            sharpe_ratio = 0.0
        
        # 计算最大回撤
        equity_series = pd.Series(self.equity_curve)
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax
        max_drawdown = abs(drawdown.min()) if len(drawdown) > 0 else 0.0
        
        # 计算胜率
        winning_trades = [t for t in self.trades if t.pnl > 0]
        total_trades = len([t for t in self.trades if t.side == OrderSide.SELL])
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0.0
        
        result = BacktestResult(
            strategy_name=self.strategy.name,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            parameters=self.strategy.get_parameters()
        )
        
        return result


def run_backtest(
    strategy: BaseStrategy,
    symbol: str,
    start_date: str,
    end_date: str,
    initial_capital: float = 10000.0
) -> BacktestResult:
    """
    便捷函数：运行回测
    
    Args:
        strategy: 策略实例
        symbol: 交易对
        start_date: 开始日期
        end_date: 结束日期
        initial_capital: 初始资金
        
    Returns:
        回测结果
    """
    engine = BacktestEngine(strategy, initial_capital)
    result = engine.run(symbol, start_date, end_date)
    
    # 保存结果到数据库
    if result:
        db_manager.insert_backtest_result(result)
    
    return result
