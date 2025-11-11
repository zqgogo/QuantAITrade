"""
任务执行日志模块
负责记录任务执行的详细日志
"""

import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from loguru import logger

from data.db_manager import db_manager


class TaskLogger:
    """任务日志记录器"""
    
    def __init__(self):
        self.db = db_manager
        self.current_instance_id = None
    
    def set_instance_id(self, instance_id: str):
        """
        设置当前实例ID
        
        Args:
            instance_id: 实例ID
        """
        self.current_instance_id = instance_id
    
    def log_task_start(
        self, 
        task_name: str, 
        task_type: str = 'scheduled',
        parameters: Optional[Dict[str, Any]] = None
    ):
        """
        记录任务开始
        
        Args:
            task_name: 任务名称
            task_type: 任务类型
            parameters: 任务参数
        """
        if not self.current_instance_id:
            logger.warning("未设置实例ID，无法记录任务日志")
            return
            
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO task_execution_log 
                (instance_id, task_name, task_type, status, start_time, result_summary)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                self.current_instance_id,
                task_name,
                task_type,
                'running',
                int(time.time()),
                json.dumps(parameters, ensure_ascii=False) if parameters else None
            ))
            conn.commit()
            task_id = cursor.lastrowid
            logger.info(f"任务开始: {task_name} (ID: {task_id})")
            return task_id
        except Exception as e:
            logger.error(f"记录任务开始失败: {e}")
            return None
    
    def log_task_end(
        self, 
        task_id: int, 
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ):
        """
        记录任务结束
        
        Args:
            task_id: 任务ID
            result: 任务结果
            error_message: 错误信息
        """
        if not self.current_instance_id:
            return
            
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        end_time = int(time.time())
        
        try:
            # 获取任务开始时间以计算耗时
            cursor.execute('''
                SELECT start_time FROM task_execution_log 
                WHERE id = ? AND instance_id = ?
            ''', (task_id, self.current_instance_id))
            row = cursor.fetchone()
            
            duration = 0
            if row:
                duration = end_time - row[0]
            
            status = 'failed' if error_message else 'success'
            
            cursor.execute('''
                UPDATE task_execution_log 
                SET status = ?, end_time = ?, duration_seconds = ?, 
                    result_summary = ?, error_message = ?
                WHERE id = ? AND instance_id = ?
            ''', (
                status,
                end_time,
                duration,
                json.dumps(result, ensure_ascii=False) if result else None,
                error_message,
                task_id,
                self.current_instance_id
            ))
            conn.commit()
            logger.info(f"任务结束: ID {task_id}, 状态: {status}, 耗时: {duration:.2f}秒")
        except Exception as e:
            logger.error(f"记录任务结束失败: {e}")
    
    def log_task_failed(
        self, 
        task_id: int, 
        error_message: str,
        retry_count: int = 0
    ):
        """
        记录任务失败
        
        Args:
            task_id: 任务ID
            error_message: 错误信息
            retry_count: 重试次数
        """
        if not self.current_instance_id:
            return
            
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE task_execution_log 
                SET status = ?, error_message = ?, retry_count = ?
                WHERE id = ? AND instance_id = ?
            ''', (
                'failed',
                error_message,
                retry_count,
                task_id,
                self.current_instance_id
            ))
            conn.commit()
            logger.error(f"任务失败: ID {task_id}, 错误: {error_message}, 重试次数: {retry_count}")
        except Exception as e:
            logger.error(f"记录任务失败失败: {e}")
    
    def get_task_history(
        self, 
        task_name: Optional[str] = None, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        查询任务历史
        
        Args:
            task_name: 任务名称(可选)
            limit: 限制数量
            
        Returns:
            任务历史列表
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            if task_name:
                cursor.execute('''
                    SELECT * FROM task_execution_log 
                    WHERE task_name = ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (task_name, limit))
            else:
                cursor.execute('''
                    SELECT * FROM task_execution_log 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"查询任务历史失败: {e}")
            return []
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """
        获取任务执行统计
        
        Returns:
            任务统计信息
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # 按任务名和状态分组统计
            cursor.execute('''
                SELECT task_name, status, COUNT(*) as count,
                       AVG(duration_seconds) as avg_duration
                FROM task_execution_log 
                GROUP BY task_name, status
                ORDER BY task_name, status
            ''')
            
            rows = cursor.fetchall()
            stats = {}
            
            for row in rows:
                task_name = row['task_name']
                if task_name not in stats:
                    stats[task_name] = {}
                
                stats[task_name][row['status']] = {
                    'count': row['count'],
                    'avg_duration': row['avg_duration'] or 0
                }
            
            return stats
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            return {}


# 全局实例
task_logger = TaskLogger()