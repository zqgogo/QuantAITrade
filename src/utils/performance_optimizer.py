"""
性能优化工具
提供数据库索引、缓存机制、批量API调用等性能优化功能
"""

import time
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from loguru import logger
from functools import wraps

from data.db_manager import db_manager


class PerformanceOptimizer:
    """性能优化器类"""
    
    def __init__(self):
        """初始化性能优化器"""
        self.cache = {}  # 简单的内存缓存
        self.cache_lock = threading.Lock()
        self.cache_stats = {'hits': 0, 'misses': 0}
        logger.info("性能优化器初始化完成")
    
    def optimize_database(self):
        """
        优化数据库性能
        
        实现方案：
        1. 创建必要的索引
        2. 分析查询计划
        3. 清理过期数据
        """
        logger.info("开始数据库性能优化...")
        
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # 1. K线数据表索引
            logger.info("创建K线数据索引...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_kline_symbol_interval_time 
                ON kline_data(symbol, interval, open_time)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_kline_close_time 
                ON kline_data(symbol, interval, close_time)
            """)
            
            # 2. 交易记录表索引
            logger.info("创建交易记录索引...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trade_symbol_time 
                ON trade_records(symbol, timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trade_status_time 
                ON trade_records(status, timestamp)
            """)
            
            # 3. 持仓表索引
            logger.info("创建持仓索引...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_position_symbol_status 
                ON positions(symbol, status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_position_status_time 
                ON positions(status, entry_time)
            """)
            
            # 4. 策略信号表索引
            logger.info("创建策略信号索引...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_signal_strategy_time 
                ON strategy_signals(strategy_name, timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_signal_symbol_type_time 
                ON strategy_signals(symbol, signal_type, timestamp)
            """)
            
            # 5. AI分析日志索引
            logger.info("创建AI分析索引...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ai_analysis_date 
                ON ai_analysis_log(analysis_date)
            """)
            
            conn.commit()
            
            # 6. 分析数据库
            logger.info("分析数据库...")
            cursor.execute("ANALYZE")
            
            logger.success("数据库优化完成")
            
            # 7. 显示索引信息
            self._show_index_info(cursor)
            
        except Exception as e:
            logger.error(f"数据库优化失败: {e}")
    
    def _show_index_info(self, cursor):
        """显示索引信息"""
        try:
            # 获取所有索引
            cursor.execute("""
                SELECT name, tbl_name 
                FROM sqlite_master 
                WHERE type='index' AND name LIKE 'idx_%'
            """)
            
            indexes = cursor.fetchall()
            logger.info(f"共创建 {len(indexes)} 个索引：")
            for idx in indexes:
                logger.info(f"  - {idx['name']} on {idx['tbl_name']}")
                
        except Exception as e:
            logger.error(f"获取索引信息失败: {e}")
    
    def cache_get(self, key: str) -> Optional[Any]:
        """
        从缓存获取数据
        
        Args:
            key: 缓存键
        
        Returns:
            缓存值或None
        """
        with self.cache_lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # 检查是否过期
                if time.time() < entry['expire_time']:
                    self.cache_stats['hits'] += 1
                    return entry['value']
                else:
                    # 过期则删除
                    del self.cache[key]
            
            self.cache_stats['misses'] += 1
            return None
    
    def cache_set(self, key: str, value: Any, ttl: int = 60):
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        with self.cache_lock:
            self.cache[key] = {
                'value': value,
                'expire_time': time.time() + ttl,
                'created_at': time.time()
            }
    
    def cache_delete(self, key: str):
        """删除缓存"""
        with self.cache_lock:
            if key in self.cache:
                del self.cache[key]
    
    def cache_clear(self):
        """清空所有缓存"""
        with self.cache_lock:
            self.cache.clear()
            self.cache_stats = {'hits': 0, 'misses': 0}
            logger.info("缓存已清空")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self.cache_lock:
            total = self.cache_stats['hits'] + self.cache_stats['misses']
            hit_rate = (self.cache_stats['hits'] / total * 100) if total > 0 else 0
            
            return {
                'cache_size': len(self.cache),
                'hits': self.cache_stats['hits'],
                'misses': self.cache_stats['misses'],
                'hit_rate': hit_rate
            }
    
    def cleanup_expired_cache(self):
        """
        清理过期缓存
        
        定期调用此方法清理过期条目
        """
        with self.cache_lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self.cache.items()
                if current_time >= entry['expire_time']
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.debug(f"清理了 {len(expired_keys)} 个过期缓存")


def cache_result(ttl: int = 60, key_func: Optional[Callable] = None):
    """
    缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒）
        key_func: 自定义缓存键生成函数
    
    使用示例：
        @cache_result(ttl=300)
        def get_market_data(symbol):
            # 耗时的数据获取操作
            return data
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认使用函数名和参数生成键
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # 尝试从缓存获取
            cached_value = performance_optimizer.cache_get(cache_key)
            if cached_value is not None:
                logger.debug(f"缓存命中: {func.__name__}")
                return cached_value
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            performance_optimizer.cache_set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def timing_decorator(func):
    """
    性能计时装饰器
    
    使用示例：
        @timing_decorator
        def slow_function():
            # 耗时操作
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = (time.time() - start_time) * 1000  # 转换为毫秒
        
        logger.debug(f"{func.__name__} 执行时间: {elapsed:.2f}ms")
        
        return result
    
    return wrapper


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, batch_size: int = 10, flush_interval: int = 5):
        """
        初始化批量处理器
        
        Args:
            batch_size: 批量大小
            flush_interval: 自动刷新间隔（秒）
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.batches: Dict[str, List] = {}
        self.last_flush_time: Dict[str, float] = {}
        self.lock = threading.Lock()
    
    def add(self, batch_key: str, item: Any):
        """
        添加项到批次
        
        Args:
            batch_key: 批次键
            item: 要添加的项
        """
        with self.lock:
            if batch_key not in self.batches:
                self.batches[batch_key] = []
                self.last_flush_time[batch_key] = time.time()
            
            self.batches[batch_key].append(item)
            
            # 检查是否需要刷新
            if len(self.batches[batch_key]) >= self.batch_size:
                return self._flush(batch_key)
            
            # 检查时间间隔
            if time.time() - self.last_flush_time[batch_key] >= self.flush_interval:
                return self._flush(batch_key)
            
            return []
    
    def _flush(self, batch_key: str) -> List:
        """刷新批次"""
        if batch_key in self.batches and self.batches[batch_key]:
            items = self.batches[batch_key]
            self.batches[batch_key] = []
            self.last_flush_time[batch_key] = time.time()
            return items
        return []
    
    def flush_all(self) -> Dict[str, List]:
        """刷新所有批次"""
        with self.lock:
            result = {}
            for batch_key in list(self.batches.keys()):
                flushed = self._flush(batch_key)
                if flushed:
                    result[batch_key] = flushed
            return result


# 全局实例
performance_optimizer = PerformanceOptimizer()
batch_processor = BatchProcessor()
