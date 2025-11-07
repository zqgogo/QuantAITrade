"""
数据获取模块
负责从Binance API获取行情数据
"""

import ccxt
import time
from typing import List, Optional
from datetime import datetime, timedelta
from loguru import logger

from config import BINANCE_API_KEY, BINANCE_API_SECRET, BINANCE_TESTNET, get_config
from data.models import KlineData
from data.db_manager import db_manager


class DataFetcher:
    """数据获取器类"""
    
    def __init__(self):
        """初始化数据获取器"""
        self.config = get_config()
        
        # 初始化Binance交易所连接
        exchange_class = ccxt.binance
        self.exchange = exchange_class({
            'apiKey': BINANCE_API_KEY,
            'secret': BINANCE_API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future' if not BINANCE_TESTNET else 'future',
            }
        })
        
        if BINANCE_TESTNET:
            self.exchange.set_sandbox_mode(True)
            logger.info("使用Binance测试网")
        
        self.retry_delay = self.config['data']['retry_delay']
        self.max_retries = self.config['data']['max_retries']
        self.max_failures = self.config.get('state_management', {}).get('data_fetch_max_failures', 5)
    
    def fetch_klines(
        self,
        symbol: str,
        interval: str = '1h',
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500
    ) -> List[KlineData]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对（如 BTCUSDT）
            interval: 时间周期
            start_time: 开始时间戳（毫秒）
            end_time: 结束时间戳（毫秒）
            limit: 限制数量
            
        Returns:
            K线数据列表
        """
        for attempt in range(self.max_retries):
            try:
                params = {}
                if start_time:
                    params['startTime'] = start_time
                if end_time:
                    params['endTime'] = end_time
                
                # 获取OHLCV数据
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol,
                    timeframe=interval,
                    since=start_time,
                    limit=limit,
                    params=params
                )
                
                # 转换为KlineData对象
                klines = []
                for candle in ohlcv:
                    kline = KlineData(
                        symbol=symbol,
                        interval=interval,
                        open_time=int(candle[0]),
                        open=float(candle[1]),
                        high=float(candle[2]),
                        low=float(candle[3]),
                        close=float(candle[4]),
                        volume=float(candle[5]),
                        close_time=int(candle[0]) + self._interval_to_milliseconds(interval) - 1,
                        quote_volume=0.0,  # ccxt不返回此字段
                        trades_count=0
                    )
                    klines.append(kline)
                
                logger.info(f"获取{symbol} {interval}数据: {len(klines)}条")
                return klines
                
            except Exception as e:
                logger.error(f"获取K线数据失败 (尝试{attempt+1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # 指数退避
                else:
                    raise
        
        return []
    
    def _interval_to_milliseconds(self, interval: str) -> int:
        """将时间周期转换为毫秒"""
        mapping = {
            '1m': 60 * 1000,
            '5m': 5 * 60 * 1000,
            '15m': 15 * 60 * 1000,
            '30m': 30 * 60 * 1000,
            '1h': 60 * 60 * 1000,
            '4h': 4 * 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000,
        }
        return mapping.get(interval, 60 * 60 * 1000)
    
    def fetch_and_store(self, symbol: str, interval: str):
        """
        获取数据并存储到数据库
        
        Args:
            symbol: 交易对
            interval: 时间周期
        """
        try:
            # 获取数据获取进度
            progress = self._get_fetch_progress(symbol, interval)
            
            # 检查是否需要暂停（连续失败次数过多）
            if progress and progress.get('consecutive_failures', 0) >= self.max_failures:
                logger.warning(f"{symbol} {interval} 连续失败次数过多，暂停获取")
                return
            
            # 根据进度确定起始时间
            if progress and progress.get('fetch_status') == 'fetching':
                # 上次获取未完成，可能中断，需要重新获取
                start_time = progress.get('last_fetch_time')
                logger.info(f"{symbol} {interval} 检测到上次获取未完成，从 {start_time} 继续")
            elif progress and progress.get('last_complete_time'):
                # 增量更新：从上次完成时间开始获取
                start_time = progress.get('last_complete_time') + self._interval_to_milliseconds(interval)
                logger.info(f"{symbol} {interval} 增量更新，起始时间: {datetime.fromtimestamp(start_time/1000)}")
            else:
                # 首次获取：回补历史数据
                backfill_days = self.config['data']['backfill_days']
                start_time = int((datetime.now() - timedelta(days=backfill_days)).timestamp() * 1000)
                logger.info(f"{symbol} {interval} 首次获取，回补{backfill_days}天数据")
            
            # 更新获取状态为进行中
            self._update_fetch_progress(symbol, interval, 'fetching', start_time)
            
            # 获取数据
            klines = self.fetch_klines(symbol, interval, start_time=start_time)
            
            if klines:
                # 批量存储
                db_manager.insert_klines_batch(klines)
                
                # 更新获取状态为完成
                last_time = max(kline.open_time for kline in klines)
                self._update_fetch_progress(symbol, interval, 'completed', last_time, len(klines))
                
                logger.success(f"{symbol} {interval} 数据更新成功: {len(klines)}条")
            else:
                # 更新获取状态为完成（无新数据）
                self._update_fetch_progress(symbol, interval, 'completed', start_time, 0)
                logger.warning(f"{symbol} {interval} 无新数据")
                
        except Exception as e:
            logger.error(f"获取并存储数据失败: {e}")
            # 记录失败并增加失败次数
            self._record_fetch_failure(symbol, interval, str(e))
            raise
    
    def _get_fetch_progress(self, symbol: str, interval: str) -> Optional[dict]:
        """
        获取数据获取进度
        
        Args:
            symbol: 交易对
            interval: 时间周期
            
        Returns:
            进度信息
        """
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT * FROM data_fetch_progress 
                WHERE symbol = ? AND interval = ?
            ''', (symbol, interval))
            
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"获取数据获取进度失败: {e}")
            return None
    
    def _update_fetch_progress(
        self, 
        symbol: str, 
        interval: str, 
        status: str, 
        last_time: int, 
        record_count: int = 0
    ):
        """
        更新数据获取进度
        
        Args:
            symbol: 交易对
            interval: 时间周期
            status: 状态
            last_time: 最后时间
            record_count: 记录数量
        """
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # 检查记录是否存在
            cursor.execute('''
                SELECT id FROM data_fetch_progress 
                WHERE symbol = ? AND interval = ?
            ''', (symbol, interval))
            
            row = cursor.fetchone()
            
            if row:
                # 更新现有记录
                cursor.execute('''
                    UPDATE data_fetch_progress 
                    SET last_fetch_time = ?, fetch_status = ?, total_records = total_records + ?,
                        consecutive_failures = 0, updated_at = strftime('%s', 'now')
                    WHERE symbol = ? AND interval = ?
                ''', (last_time, status, record_count, symbol, interval))
            else:
                # 插入新记录
                cursor.execute('''
                    INSERT INTO data_fetch_progress 
                    (symbol, interval, last_fetch_time, fetch_status, total_records)
                    VALUES (?, ?, ?, ?, ?)
                ''', (symbol, interval, last_time, status, record_count))
            
            conn.commit()
        except Exception as e:
            logger.error(f"更新数据获取进度失败: {e}")
    
    def _record_fetch_failure(self, symbol: str, interval: str, error: str):
        """
        记录数据获取失败
        
        Args:
            symbol: 交易对
            interval: 时间周期
            error: 错误信息
        """
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # 更新失败次数
            cursor.execute('''
                UPDATE data_fetch_progress 
                SET last_error = ?, consecutive_failures = consecutive_failures + 1,
                    fetch_status = 'failed', updated_at = strftime('%s', 'now')
                WHERE symbol = ? AND interval = ?
            ''', (error, symbol, interval))
            
            # 如果没有记录，则插入新记录
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO data_fetch_progress 
                    (symbol, interval, fetch_status, last_error, consecutive_failures)
                    VALUES (?, ?, ?, ?, ?)
                ''', (symbol, interval, 'failed', error, 1))
            
            conn.commit()
        except Exception as e:
            logger.error(f"记录数据获取失败失败: {e}")
    
    def recover_progress(self, progress: dict):
        """
        恢复数据获取进度（用于系统恢复）
        
        Args:
            progress: 进度信息
        """
        # 这里可以实现具体的进度恢复逻辑
        # 目前只是记录日志
        logger.info(f"恢复数据获取进度: {progress['symbol']} {progress['interval']}")

# 全局数据获取器实例
data_fetcher = DataFetcher()
