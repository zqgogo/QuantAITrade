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
            # 获取最新时间戳
            latest_time = db_manager.get_latest_kline_time(symbol, interval)
            
            if latest_time:
                # 增量更新：从最新时间开始获取
                start_time = latest_time + self._interval_to_milliseconds(interval)
                logger.info(f"{symbol} {interval} 增量更新，起始时间: {datetime.fromtimestamp(start_time/1000)}")
            else:
                # 首次获取：回补历史数据
                backfill_days = self.config['data']['backfill_days']
                start_time = int((datetime.now() - timedelta(days=backfill_days)).timestamp() * 1000)
                logger.info(f"{symbol} {interval} 首次获取，回补{backfill_days}天数据")
            
            # 获取数据
            klines = self.fetch_klines(symbol, interval, start_time=start_time)
            
            if klines:
                # 批量存储
                db_manager.insert_klines_batch(klines)
                logger.success(f"{symbol} {interval} 数据更新成功: {len(klines)}条")
            else:
                logger.warning(f"{symbol} {interval} 无新数据")
                
        except Exception as e:
            logger.error(f"获取并存储数据失败: {e}")
            raise
    
    def fetch_all_configured_symbols(self):
        """获取所有配置的交易对数据"""
        symbols = self.config['trading']['symbols']
        intervals = self.config['trading']['intervals']
        
        logger.info(f"开始获取数据: {len(symbols)}个交易对，{len(intervals)}个周期")
        
        for symbol in symbols:
            for interval in intervals:
                try:
                    self.fetch_and_store(symbol, interval)
                    time.sleep(0.5)  # 避免API限流
                except Exception as e:
                    logger.error(f"获取{symbol} {interval}失败: {e}")
                    continue
        
        logger.success("所有数据获取完成")
    
    def get_current_price(self, symbol: str) -> float:
        """
        获取当前市场价格
        
        Args:
            symbol: 交易对
            
        Returns:
            当前价格
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return float(ticker['last'])
        except Exception as e:
            logger.error(f"获取价格失败: {e}")
            raise


# 全局数据获取器实例
data_fetcher = DataFetcher()
