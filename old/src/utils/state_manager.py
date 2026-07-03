"""
系统状态管理模块
负责管理系统运行状态的持久化和恢复
"""

import uuid
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger

from data.db_manager import db_manager
from config.settings import get_config


class SystemState:
    """系统状态类"""
    
    def __init__(self):
        self.db = db_manager
        self.current_instance_id = None
        self.config = get_config()
    
    def create_instance(self, run_mode: str) -> str:
        """
        创建新的运行实例
        
        Args:
            run_mode: 运行模式 (manual/auto/hybrid)
            
        Returns:
            instance_id: 实例ID
        """
        instance_id = str(uuid.uuid4())
        self.current_instance_id = instance_id
        
        try:
            # 获取当前配置快照
            config_snapshot = json.dumps(self.config, ensure_ascii=False)
        except Exception as e:
            logger.error(f"序列化配置失败: {e}")
            config_snapshot = "{}"
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO system_state 
                (instance_id, run_mode, status, start_time, pid, config_snapshot)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                instance_id,
                run_mode,
                'running',
                int(time.time()),
                self.config.get('process', {}).get('pid', 0),
                config_snapshot
            ))
            conn.commit()
            logger.info(f"创建系统实例: {instance_id}, 运行模式: {run_mode}")
        except Exception as e:
            logger.error(f"创建系统实例失败: {e}")
            # 不抛出异常，继续运行
        
        return instance_id
    
    def update_heartbeat(self):
        """更新心跳时间"""
        if not self.current_instance_id:
            return
            
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE system_state 
                SET heartbeat_time = ?
                WHERE instance_id = ?
            ''', (int(time.time()), self.current_instance_id))
            conn.commit()
        except Exception as e:
            logger.error(f"更新心跳时间失败: {e}")
            # 不抛出异常，继续运行
    
    def mark_stopped(self, stop_reason: str = 'manual'):
        """
        标记系统停止
        
        Args:
            stop_reason: 停止原因
        """
        if not self.current_instance_id:
            return
            
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE system_state 
                SET status = ?, stop_time = ?, stop_reason = ?
                WHERE instance_id = ?
            ''', ('stopped', int(time.time()), stop_reason, self.current_instance_id))
            conn.commit()
            logger.info(f"系统实例 {self.current_instance_id} 已标记为停止, 原因: {stop_reason}")
        except Exception as e:
            logger.error(f"标记系统停止失败: {e}")
            # 不抛出异常，继续运行
    
    def mark_crashed(self, error_message: str = ''):
        """
        标记系统崩溃
        
        Args:
            error_message: 错误信息
        """
        if not self.current_instance_id:
            return
            
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE system_state 
                SET status = ?, stop_time = ?, stop_reason = ?
                WHERE instance_id = ?
            ''', ('crashed', int(time.time()), f'crash: {error_message}', self.current_instance_id))
            conn.commit()
            logger.critical(f"系统实例 {self.current_instance_id} 已标记为崩溃, 错误: {error_message}")
        except Exception as e:
            logger.error(f"标记系统崩溃失败: {e}")
            # 不抛出异常，继续运行
    
    def get_last_instance(self) -> Optional[Dict[str, Any]]:
        """
        获取上次运行记录
        
        Returns:
            上次运行记录或None
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT * FROM system_state 
                ORDER BY start_time DESC 
                LIMIT 1
            ''')
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"获取上次运行记录失败: {e}")
            return None
    
    def is_last_crashed(self) -> bool:
        """
        判断上次是否异常关闭
        
        Returns:
            bool: True表示异常关闭，False表示正常关闭
        """
        try:
            last_instance = self.get_last_instance()
            if not last_instance:
                return False
            
            # 如果状态是running且心跳时间超过5分钟，则判定为异常关闭
            if (last_instance['status'] == 'running' and 
                last_instance['heartbeat_time'] and 
                (int(time.time()) - last_instance['heartbeat_time']) > 300):  # 5分钟
                return True
            
            # 如果状态是crashed，则判定为异常关闭
            if last_instance['status'] == 'crashed':
                return True
            
            return False
        except Exception as e:
            logger.error(f"检查上次是否异常关闭失败: {e}")
            return False


# 全局实例
state_manager = SystemState()