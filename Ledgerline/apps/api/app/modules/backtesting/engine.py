from datetime import datetime
from typing import List

import numpy as np

from app.modules.backtesting.schemas import EquityCurvePoint, PerformanceMetrics, TradeRecord


class BacktestEngine:
    def __init__(self):
        self.equity_curve: List[EquityCurvePoint] = []
        self.trades: List[TradeRecord] = []
        self.balance: float = 0.0
        self.equity: float = 0.0
        self.initial_capital: float = 0.0
        self.position: float = 0.0
        self.position_value: float = 0.0
        self.last_trade_price: float = 0.0
        self.cumulative_pnl: float = 0.0
        self.commission_rate: float = 0.0
        self.position_size: float = 0.0
    
    def initialize(self, initial_capital: float, commission_rate: float, position_size: float):
        self.balance = initial_capital
        self.equity = initial_capital
        self.initial_capital = initial_capital
        self.position = 0.0
        self.position_value = 0.0
        self.last_trade_price = 0.0
        self.cumulative_pnl = 0.0
        self.commission_rate = commission_rate
        self.position_size = position_size
        self.equity_curve = []
        self.trades = []
    
    def update_equity(self, price: float, timestamp: datetime):
        self.position_value = self.position * price
        self.equity = self.balance + self.position_value
        self.equity_curve.append(EquityCurvePoint(
            timestamp=timestamp,
            equity=self.equity,
            returns=(self.equity - self.initial_capital) / self.initial_capital * 100,
        ))
    
    def execute_trade(self, timestamp: datetime, signal_type: str, price: float):
        if signal_type == "buy" and self.position == 0:
            amount = self.equity * self.position_size
            commission = amount * self.commission_rate
            quantity = (amount - commission) / price
            self.balance -= amount
            self.position = quantity
            self.last_trade_price = price
            
            trade = TradeRecord(
                timestamp=timestamp,
                type="buy",
                price=price,
                quantity=quantity,
                amount=amount,
                commission=commission,
                balance=self.balance,
                pnl=0,
                pnl_cumulative=self.cumulative_pnl,
            )
            self.trades.append(trade)
        
        elif signal_type == "sell" and self.position > 0:
            amount = self.position * price
            commission = amount * self.commission_rate
            proceeds = amount - commission
            pnl = proceeds - (self.position * self.last_trade_price)
            self.cumulative_pnl += pnl
            self.balance += proceeds
            self.position = 0
            
            trade = TradeRecord(
                timestamp=timestamp,
                type="sell",
                price=price,
                quantity=self.position,
                amount=amount,
                commission=commission,
                balance=self.balance,
                pnl=pnl,
                pnl_cumulative=self.cumulative_pnl,
            )
            self.trades.append(trade)


class PerformanceCalculator:
    @staticmethod
    def calculate_metrics(
        trades: List[TradeRecord],
        equity_curve: List[EquityCurvePoint],
        initial_capital: float,
        start_date: datetime,
        end_date: datetime,
    ) -> PerformanceMetrics:
        if not trades:
            return PerformanceMetrics(
                total_return=0,
                annualized_return=0,
                max_drawdown=0,
                sharpe_ratio=0,
                sortino_ratio=0,
                win_rate=0,
                profit_factor=0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                avg_win=0,
                avg_loss=0,
                best_trade=0,
                worst_trade=0,
            )
        
        trade_pnls = [t.pnl for t in trades if t.type == "sell"]
        winning_trades = [p for p in trade_pnls if p > 0]
        losing_trades = [p for p in trade_pnls if p <= 0]
        
        total_return = ((equity_curve[-1].equity - initial_capital) / initial_capital) * 100
        
        duration_days = (end_date - start_date).days
        years = duration_days / 365.25 if duration_days > 0 else 1
        annualized_return = ((1 + total_return / 100) ** (1 / years) - 1) * 100
        
        equity_values = [ec.equity for ec in equity_curve]
        running_max = np.maximum.accumulate(equity_values)
        drawdowns = (equity_values - running_max) / running_max * 100
        max_drawdown = np.min(drawdowns) if len(drawdowns) > 0 else 0
        
        period_returns = []
        for i in range(1, len(equity_curve)):
            prev_eq = equity_curve[i-1].equity
            curr_eq = equity_curve[i].equity
            period_returns.append((curr_eq - prev_eq) / prev_eq)
        
        period_returns_np = np.array(period_returns)
        sharpe_ratio = 0
        sortino_ratio = 0
        
        if len(period_returns_np) > 0:
            std_dev = np.std(period_returns_np)
            mean_return = np.mean(period_returns_np)
            
            if std_dev > 0:
                sharpe_ratio = mean_return / std_dev * np.sqrt(252)
            
            downside_returns = period_returns_np[period_returns_np < 0]
            downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0
            if downside_std > 0:
                sortino_ratio = mean_return / downside_std * np.sqrt(252)
        
        win_rate = (len(winning_trades) / len(trade_pnls)) * 100 if trade_pnls else 0
        
        total_profit = sum(winning_trades)
        total_loss = abs(sum(losing_trades))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        avg_win = sum(winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(losing_trades) / len(losing_trades) if losing_trades else 0
        
        best_trade = max(trade_pnls) if trade_pnls else 0
        worst_trade = min(trade_pnls) if trade_pnls else 0
        
        return PerformanceMetrics(
            total_return=round(total_return, 2),
            annualized_return=round(annualized_return, 2),
            max_drawdown=round(max_drawdown, 2),
            sharpe_ratio=round(sharpe_ratio, 2),
            sortino_ratio=round(sortino_ratio, 2),
            win_rate=round(win_rate, 2),
            profit_factor=round(profit_factor, 2),
            total_trades=len(trades) // 2,
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            avg_win=round(avg_win, 2),
            avg_loss=round(avg_loss, 2),
            best_trade=round(best_trade, 2),
            worst_trade=round(worst_trade, 2),
        )
