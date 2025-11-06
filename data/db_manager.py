"""
数据库管理模块
负责SQLite数据库的创建、连接和操作
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from loguru import logger

from config import DATABASE_PATH
from data.models import (
    KlineData, Signal, TradeRecord, AIAnalysis, BacktestResult,
    SignalType, OrderSide, OrderStatus, StopLossType
)


class DatabaseManager:
    """数据库管理器类"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = None
        
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self._connection is None:
            self._connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            # 启用WAL模式提升并发性能
            self._connection.execute("PRAGMA journal_mode=WAL")
            # 返回字典格式的行
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    def close(self):
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 创建K线数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kline_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                interval TEXT NOT NULL,
                open_time INTEGER NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL NOT NULL,
                close_time INTEGER NOT NULL,
                quote_volume REAL DEFAULT 0.0,
                trades_count INTEGER DEFAULT 0,
                created_at INTEGER DEFAULT (strftime('%s', 'now')),
                UNIQUE(symbol, interval, open_time)
            )
        ''')
        
        # 创建索引
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_kline_symbol_interval 
            ON kline_data(symbol, interval, open_time DESC)
        ''')
        
        # 创建策略信号表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategy_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                price REAL NOT NULL,
                timestamp INTEGER NOT NULL,
                parameters TEXT,
                confidence REAL DEFAULT 0.0,
                reason TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_signals_timestamp 
            ON strategy_signals(timestamp DESC)
        ''')
        
        # 创建交易记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                order_type TEXT NOT NULL,
                price REAL NOT NULL,
                quantity REAL NOT NULL,
                status TEXT NOT NULL,
                order_id TEXT,
                strategy_name TEXT NOT NULL,
                stop_loss_price REAL,
                stop_loss_type TEXT,
                timestamp INTEGER NOT NULL,
                pnl REAL DEFAULT 0.0,
                pnl_percent REAL DEFAULT 0.0
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_trades_timestamp 
            ON trade_records(timestamp DESC)
        ''')
        
        # 创建持仓表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                entry_price REAL NOT NULL,
                quantity REAL NOT NULL,
                strategy_name TEXT NOT NULL,
                stop_loss_type TEXT NOT NULL,
                stop_loss_price REAL NOT NULL,
                initial_stop_price REAL NOT NULL,
                highest_price REAL NOT NULL,
                entry_time INTEGER NOT NULL,
                unrealized_pnl REAL DEFAULT 0.0,
                unrealized_pnl_percent REAL DEFAULT 0.0,
                is_closed INTEGER DEFAULT 0,
                UNIQUE(symbol, strategy_name, is_closed)
            )
        ''')
        
        # 创建AI分析记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_analysis_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_date TEXT NOT NULL,
                market_summary TEXT,
                suggestions TEXT,
                risk_alert TEXT,
                model_version TEXT,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        ''')
        
        # 创建回测结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                initial_capital REAL NOT NULL,
                final_capital REAL NOT NULL,
                total_return REAL NOT NULL,
                sharpe_ratio REAL DEFAULT 0.0,
                max_drawdown REAL DEFAULT 0.0,
                win_rate REAL DEFAULT 0.0,
                parameters TEXT,
                created_at INTEGER DEFAULT (strftime('%s', 'now'))
            )
        ''')
        
        conn.commit()
        logger.info(f"数据库初始化完成: {self.db_path}")
    
    # ========== K线数据操作 ==========
    
    def insert_kline(self, kline: KlineData):
        """插入K线数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO kline_data 
                (symbol, interval, open_time, open, high, low, close, volume, 
                 close_time, quote_volume, trades_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                kline.symbol, kline.interval, kline.open_time,
                kline.open, kline.high, kline.low, kline.close, kline.volume,
                kline.close_time, kline.quote_volume, kline.trades_count,
                kline.created_at
            ))
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"插入K线数据失败: {e}")
            raise
    
    def insert_klines_batch(self, klines: List[KlineData]):
        """批量插入K线数据"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            data = [
                (k.symbol, k.interval, k.open_time, k.open, k.high, k.low,
                 k.close, k.volume, k.close_time, k.quote_volume,
                 k.trades_count, k.created_at)
                for k in klines
            ]
            
            cursor.executemany('''
                INSERT OR IGNORE INTO kline_data 
                (symbol, interval, open_time, open, high, low, close, volume,
                 close_time, quote_volume, trades_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', data)
            
            conn.commit()
            logger.info(f"批量插入K线数据: {len(klines)}条")
        except sqlite3.Error as e:
            logger.error(f"批量插入K线数据失败: {e}")
            raise
    
    def get_latest_kline_time(self, symbol: str, interval: str) -> Optional[int]:
        """获取最新的K线时间戳"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT MAX(open_time) FROM kline_data 
            WHERE symbol = ? AND interval = ?
        ''', (symbol, interval))
        
        result = cursor.fetchone()
        return result[0] if result[0] else None
    
    def get_klines(
        self, 
        symbol: str, 
        interval: str, 
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对
            interval: 时间周期
            start_time: 开始时间戳
            end_time: 结束时间戳
            limit: 限制数量
            
        Returns:
            K线数据列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT * FROM kline_data 
            WHERE symbol = ? AND interval = ?
        '''
        params = [symbol, interval]
        
        if start_time:
            query += ' AND open_time >= ?'
            params.append(start_time)
        
        if end_time:
            query += ' AND open_time <= ?'
            params.append(end_time)
        
        query += ' ORDER BY open_time ASC'
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    # ========== 信号操作 ==========
    
    def insert_signal(self, signal: Signal):
        """插入交易信号"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO strategy_signals 
                (strategy_name, symbol, signal_type, price, timestamp, 
                 parameters, confidence, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal.strategy_name, signal.symbol, signal.signal_type.value,
                signal.price, signal.timestamp, json.dumps(signal.parameters),
                signal.confidence, signal.reason
            ))
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"插入信号失败: {e}")
            raise
    
    # ========== 交易记录操作 ==========
    
    def insert_trade(self, trade: TradeRecord) -> int:
        """插入交易记录并返回ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO trade_records 
                (symbol, side, order_type, price, quantity, status, order_id,
                 strategy_name, stop_loss_price, stop_loss_type, timestamp, pnl, pnl_percent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade.symbol, trade.side.value, trade.order_type, trade.price,
                trade.quantity, trade.status.value, trade.order_id, trade.strategy_name,
                trade.stop_loss_price, 
                trade.stop_loss_type.value if trade.stop_loss_type else None,
                trade.timestamp, trade.pnl, trade.pnl_percent
            ))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"插入交易记录失败: {e}")
            raise
    
    # ========== AI分析操作 ==========
    
    def insert_ai_analysis(self, analysis: AIAnalysis):
        """插入AI分析记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO ai_analysis_log 
                (analysis_date, market_summary, suggestions, risk_alert, 
                 model_version, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                analysis.analysis_date, analysis.market_summary,
                json.dumps(analysis.suggestions, ensure_ascii=False),
                analysis.risk_alert, analysis.model_version, analysis.created_at
            ))
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"插入AI分析失败: {e}")
            raise
    
    # ========== 回测结果操作 ==========
    
    def insert_backtest_result(self, result: BacktestResult):
        """插入回测结果"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO backtest_results 
                (strategy_name, symbol, start_date, end_date, initial_capital,
                 final_capital, total_return, sharpe_ratio, max_drawdown, 
                 win_rate, parameters, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.strategy_name, result.symbol, result.start_date,
                result.end_date, result.initial_capital, result.final_capital,
                result.total_return, result.sharpe_ratio, result.max_drawdown,
                result.win_rate, json.dumps(result.parameters), result.created_at
            ))
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"插入回测结果失败: {e}")
            raise


# 全局数据库管理器实例
db_manager = DatabaseManager()
