"""
AI数据准备模块
为AI分析准备结构化的市场数据和交易数据
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from data.db_manager import db_manager
from config import get_config


class AIDataPreparer:
    """AI数据准备器类"""
    
    def __init__(self):
        """初始化数据准备器"""
        self.config = get_config()
        logger.info("AI数据准备器初始化完成")
    
    def prepare_daily_analysis_data(self, date: str, lookback_days: int = 7) -> Optional[Dict[str, Any]]:
        """
        准备每日分析所需的数据
        
        Args:
            date: 分析日期 'YYYY-MM-DD'
            lookback_days: 回看天数
        
        Returns:
            dict: 结构化的分析数据
        """
        try:
            logger.info(f"准备AI分析数据: {date} (回看{lookback_days}天)")
            
            # 1. 市场行情数据
            market_data = self._prepare_market_data(lookback_days)
            
            # 2. 技术指标数据
            technical_indicators = self._prepare_technical_indicators(lookback_days)
            
            # 3. 交易记录数据
            trading_records = self._prepare_trading_records(lookback_days)
            
            # 4. 持仓情况
            position_data = self._prepare_position_data()
            
            # 5. 策略绩效
            strategy_performance = self._prepare_strategy_performance(lookback_days)
            
            # 6. 市场异常事件
            market_events = self._detect_market_events(lookback_days)
            
            data = {
                'analysis_date': date,
                'lookback_days': lookback_days,
                'market_data': market_data,
                'technical_indicators': technical_indicators,
                'trading_records': trading_records,
                'position_data': position_data,
                'strategy_performance': strategy_performance,
                'market_events': market_events,
                'summary_stats': self._calculate_summary_stats(market_data, trading_records)
            }
            
            logger.success(f"AI分析数据准备完成")
            return data
            
        except Exception as e:
            logger.error(f"准备AI分析数据失败: {e}")
            return None
    
    def _prepare_market_data(self, days: int) -> Dict[str, Any]:
        """准备市场行情数据"""
        try:
            symbols = self.config['trading']['symbols']
            market_data = {}
            
            for symbol in symbols:
                # 获取最近N天的1小时K线数据
                klines = db_manager.get_klines(symbol, '1h', limit=days*24)
                
                if not klines:
                    logger.warning(f"{symbol} 无市场数据")
                    continue
                
                df = pd.DataFrame(klines)
                
                # 计算关键指标
                latest_price = float(df.iloc[-1]['close'])
                price_change_1d = self._calculate_price_change(df, 24)  # 24小时
                price_change_7d = self._calculate_price_change(df, min(days*24, len(df)))
                
                volatility = self._calculate_volatility(df)
                volume_trend = self._analyze_volume_trend(df)
                
                market_data[symbol] = {
                    'latest_price': latest_price,
                    'price_change_24h': price_change_1d,
                    'price_change_7d': price_change_7d,
                    'volatility': volatility,
                    'volume_trend': volume_trend,
                    'data_points': len(df)
                }
            
            return market_data
            
        except Exception as e:
            logger.error(f"准备市场数据失败: {e}")
            return {}
    
    def _prepare_technical_indicators(self, days: int) -> Dict[str, Any]:
        """准备技术指标数据"""
        try:
            symbols = self.config['trading']['symbols']
            indicators = {}
            
            for symbol in symbols:
                klines = db_manager.get_klines(symbol, '1h', limit=days*24)
                if not klines:
                    continue
                
                df = pd.DataFrame(klines)
                df['close'] = df['close'].astype(float)
                
                # 计算常用技术指标
                indicators[symbol] = {
                    'ma5': float(df['close'].tail(5).mean()),
                    'ma20': float(df['close'].tail(20).mean()) if len(df) >= 20 else None,
                    'rsi': self._calculate_rsi(df, 14),
                    'trend': self._identify_trend(df)
                }
            
            return indicators
            
        except Exception as e:
            logger.error(f"准备技术指标失败: {e}")
            return {}
    
    def _prepare_trading_records(self, days: int) -> Dict[str, Any]:
        """准备交易记录数据"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # 获取最近N天的交易记录
            start_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
            
            cursor.execute(
                """
                SELECT symbol, side, price, quantity, status, timestamp
                FROM trade_records
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                """,
                (start_timestamp,)
            )
            
            records = cursor.fetchall()
            
            if not records:
                return {'total_trades': 0, 'records': []}
            
            # 统计分析
            trades_df = pd.DataFrame([dict(r) for r in records])
            
            total_trades = len(trades_df)
            successful_trades = len(trades_df[trades_df['status'] == 'FILLED'])
            success_rate = successful_trades / total_trades if total_trades > 0 else 0
            
            # 按交易对分组统计
            by_symbol = trades_df.groupby('symbol').size().to_dict()
            
            return {
                'total_trades': total_trades,
                'successful_trades': successful_trades,
                'success_rate': success_rate,
                'trades_by_symbol': by_symbol,
                'recent_records': [dict(r) for r in records[:10]]  # 最近10条
            }
            
        except Exception as e:
            logger.error(f"准备交易记录失败: {e}")
            return {'total_trades': 0}
    
    def _prepare_position_data(self) -> Dict[str, Any]:
        """准备持仓数据"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # 获取所有开仓持仓
            cursor.execute(
                """
                SELECT symbol, entry_price, quantity, unrealized_pnl, 
                       unrealized_pnl_percent, stop_loss_price, entry_time
                FROM positions
                WHERE status = 'OPEN'
                """
            )
            
            positions = cursor.fetchall()
            
            if not positions:
                return {'total_positions': 0, 'total_exposure': 0}
            
            positions_list = [dict(p) for p in positions]
            
            # 计算总敞口
            total_exposure = sum(p['entry_price'] * p['quantity'] for p in positions_list)
            total_pnl = sum(p['unrealized_pnl'] for p in positions_list)
            
            return {
                'total_positions': len(positions_list),
                'total_exposure': total_exposure,
                'total_unrealized_pnl': total_pnl,
                'positions': positions_list
            }
            
        except Exception as e:
            logger.error(f"准备持仓数据失败: {e}")
            return {'total_positions': 0}
    
    def _prepare_strategy_performance(self, days: int) -> Dict[str, Any]:
        """准备策略绩效数据"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            start_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
            
            # 获取策略信号统计
            cursor.execute(
                """
                SELECT strategy_name, signal_type, COUNT(*) as count
                FROM strategy_signals
                WHERE timestamp >= ?
                GROUP BY strategy_name, signal_type
                """,
                (start_timestamp,)
            )
            
            signals = cursor.fetchall()
            
            signal_stats = {}
            for row in signals:
                strategy = row['strategy_name']
                if strategy not in signal_stats:
                    signal_stats[strategy] = {'BUY': 0, 'SELL': 0}
                signal_stats[strategy][row['signal_type']] = row['count']
            
            return {
                'signal_statistics': signal_stats,
                'lookback_days': days
            }
            
        except Exception as e:
            logger.error(f"准备策略绩效失败: {e}")
            return {}
    
    def _detect_market_events(self, days: int) -> List[Dict[str, Any]]:
        """检测市场异常事件"""
        try:
            events = []
            symbols = self.config['trading']['symbols']
            
            for symbol in symbols:
                klines = db_manager.get_klines(symbol, '1h', limit=days*24)
                if not klines:
                    continue
                
                df = pd.DataFrame(klines)
                df['close'] = df['close'].astype(float)
                df['volume'] = df['volume'].astype(float)
                
                # 检测大幅波动
                df['returns'] = df['close'].pct_change()
                large_moves = df[abs(df['returns']) > 0.05]  # 5%以上波动
                
                for idx, row in large_moves.iterrows():
                    events.append({
                        'symbol': symbol,
                        'type': 'large_price_move',
                        'timestamp': row['timestamp'],
                        'price_change': float(row['returns']),
                        'description': f"{symbol} 价格变动 {row['returns']*100:.2f}%"
                    })
                
                # 检测异常交易量
                volume_mean = df['volume'].mean()
                volume_std = df['volume'].std()
                large_volume = df[df['volume'] > volume_mean + 2*volume_std]
                
                for idx, row in large_volume.iterrows():
                    events.append({
                        'symbol': symbol,
                        'type': 'large_volume',
                        'timestamp': row['timestamp'],
                        'volume': float(row['volume']),
                        'description': f"{symbol} 异常交易量"
                    })
            
            # 按时间排序，最近的在前
            events.sort(key=lambda x: x['timestamp'], reverse=True)
            return events[:20]  # 返回最近20个事件
            
        except Exception as e:
            logger.error(f"检测市场事件失败: {e}")
            return []
    
    def _calculate_summary_stats(self, market_data: Dict, trading_records: Dict) -> Dict[str, Any]:
        """计算汇总统计数据"""
        try:
            # 市场总览
            total_symbols = len(market_data)
            avg_volatility = np.mean([v['volatility'] for v in market_data.values()]) if market_data else 0
            
            # 交易统计
            total_trades = trading_records.get('total_trades', 0)
            success_rate = trading_records.get('success_rate', 0)
            
            return {
                'total_symbols_tracked': total_symbols,
                'average_market_volatility': avg_volatility,
                'total_trades': total_trades,
                'trade_success_rate': success_rate,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"计算汇总统计失败: {e}")
            return {}
    
    # ==================== 辅助计算函数 ====================
    
    def _calculate_price_change(self, df: pd.DataFrame, periods: int) -> float:
        """计算价格变化百分比"""
        if len(df) < periods:
            return 0.0
        
        start_price = float(df.iloc[-periods]['close'])
        end_price = float(df.iloc[-1]['close'])
        return (end_price / start_price - 1) * 100
    
    def _calculate_volatility(self, df: pd.DataFrame) -> float:
        """计算波动率"""
        if len(df) < 2:
            return 0.0
        
        df = df.copy()
        df['close'] = df['close'].astype(float)
        returns = df['close'].pct_change().dropna()
        return float(returns.std() * np.sqrt(24) * 100)  # 年化波动率
    
    def _analyze_volume_trend(self, df: pd.DataFrame) -> str:
        """分析成交量趋势"""
        if len(df) < 10:
            return 'insufficient_data'
        
        df = df.copy()
        df['volume'] = df['volume'].astype(float)
        
        recent_volume = df.tail(24)['volume'].mean()  # 最近24小时
        historical_volume = df.head(len(df)-24)['volume'].mean()  # 之前的
        
        if recent_volume > historical_volume * 1.2:
            return 'increasing'
        elif recent_volume < historical_volume * 0.8:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> Optional[float]:
        """计算RSI指标"""
        if len(df) < period + 1:
            return None
        
        df = df.copy()
        df['close'] = df['close'].astype(float)
        delta = df['close'].diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
    
    def _identify_trend(self, df: pd.DataFrame) -> str:
        """识别价格趋势"""
        if len(df) < 20:
            return 'unknown'
        
        df = df.copy()
        df['close'] = df['close'].astype(float)
        
        # 使用简单移动平均线判断
        ma5 = df['close'].tail(5).mean()
        ma20 = df['close'].tail(20).mean()
        
        if ma5 > ma20 * 1.02:
            return 'uptrend'
        elif ma5 < ma20 * 0.98:
            return 'downtrend'
        else:
            return 'sideways'


# 全局实例
ai_data_preparer = AIDataPreparer()
