"""
信号队列管理模块
负责管理信号的持久化队列和过期处理
"""

import uuid
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from data.db_manager import db_manager
from data.models import Signal, SignalType
from config.settings import get_config


class SignalQueueManager:
    """信号队列管理器"""
    
    def __init__(self):
        self.db = db_manager
        config = get_config()
        self.signal_expiry_minutes = config.get('state_management', {}).get('signal_expiry_minutes', 15)
    
    def enqueue_signal(self, signal: Signal) -> str:
        """
        信号入队(保存到数据库)
        
        Args:
            signal: 交易信号
            
        Returns:
            signal_id: 信号ID
        """
        signal_id = str(uuid.uuid4())
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # 计算过期时间
        expiry_time = int(time.time()) + (self.signal_expiry_minutes * 60)
        
        try:
            cursor.execute('''
                INSERT INTO signal_queue 
                (signal_id, strategy_name, symbol, signal_type, price, confidence,
                 signal_timestamp, queue_status, priority, submitted_time, expiry_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal_id,
                signal.strategy_name,
                signal.symbol,
                signal.signal_type.value,
                signal.price,
                signal.confidence,
                signal.timestamp,
                'pending',
                int(signal.confidence * 100),  # 优先级与置信度关联
                int(time.time()),
                expiry_time
            ))
            conn.commit()
            logger.info(f"信号入队: {signal_id}, 策略: {signal.strategy_name}, 类型: {signal.signal_type.value}")
            return signal_id
        except Exception as e:
            logger.error(f"信号入队失败: {e}")
            raise
    
    def dequeue_signals(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        批量加载待处理信号
        
        Args:
            limit: 限制数量
            
        Returns:
            待处理信号列表
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取未过期的待处理信号
            current_time = int(time.time())
            cursor.execute('''
                SELECT * FROM signal_queue 
                WHERE queue_status = 'pending' 
                AND (expiry_time IS NULL OR expiry_time > ?)
                ORDER BY priority DESC, submitted_time ASC
                LIMIT ?
            ''', (current_time, limit))
            
            rows = cursor.fetchall()
            signals = [dict(row) for row in rows]
            
            # 更新这些信号的状态为处理中
            if signals:
                signal_ids = [s['signal_id'] for s in signals]
                placeholders = ','.join(['?' for _ in signal_ids])
                cursor.execute(f'''
                    UPDATE signal_queue 
                    SET queue_status = 'processing', processed_time = ?
                    WHERE signal_id IN ({placeholders})
                ''', [int(time.time())] + signal_ids)
                conn.commit()
            
            logger.info(f"从队列中加载 {len(signals)} 个待处理信号")
            return signals
        except Exception as e:
            logger.error(f"加载待处理信号失败: {e}")
            return []
    
    def mark_signal_processing(self, signal_id: str):
        """
        标记信号处理中
        
        Args:
            signal_id: 信号ID
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE signal_queue 
                SET queue_status = 'processing', processed_time = ?
                WHERE signal_id = ?
            ''', (int(time.time()), signal_id))
            conn.commit()
        except Exception as e:
            logger.error(f"标记信号处理中失败: {e}")
    
    def mark_signal_completed(self, signal_id: str, order_id: Optional[str] = None):
        """
        标记信号完成
        
        Args:
            signal_id: 信号ID
            order_id: 关联的订单ID
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE signal_queue 
                SET queue_status = 'completed', order_id = ?
                WHERE signal_id = ?
            ''', (order_id, signal_id))
            conn.commit()
            logger.info(f"信号完成: {signal_id}, 订单ID: {order_id}")
        except Exception as e:
            logger.error(f"标记信号完成失败: {e}")
    
    def mark_signal_failed(self, signal_id: str, failure_reason: str):
        """
        标记信号失败
        
        Args:
            signal_id: 信号ID
            failure_reason: 失败原因
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE signal_queue 
                SET queue_status = 'failed', failure_reason = ?
                WHERE signal_id = ?
            ''', (failure_reason, signal_id))
            conn.commit()
            logger.error(f"信号失败: {signal_id}, 原因: {failure_reason}")
        except Exception as e:
            logger.error(f"标记信号失败失败: {e}")
    
    def expire_old_signals(self):
        """
        清理过期信号
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            current_time = int(time.time())
            cursor.execute('''
                UPDATE signal_queue 
                SET queue_status = 'expired'
                WHERE queue_status = 'pending' AND expiry_time < ?
            ''', (current_time,))
            
            expired_count = cursor.rowcount
            conn.commit()
            
            if expired_count > 0:
                logger.info(f"清理了 {expired_count} 个过期信号")
        except Exception as e:
            logger.error(f"清理过期信号失败: {e}")
    
    def get_queue_status(self) -> Dict[str, int]:
        """
        获取队列状态统计
        
        Returns:
            队列状态统计
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT queue_status, COUNT(*) as count
                FROM signal_queue
                GROUP BY queue_status
            ''')
            
            rows = cursor.fetchall()
            status = {row['queue_status']: row['count'] for row in rows}
            return status
        except Exception as e:
            logger.error(f"获取队列状态统计失败: {e}")
            return {}


# 全局实例
signal_queue_manager = SignalQueueManager()