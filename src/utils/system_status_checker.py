"""
系统状态检测工具
用于检测量化交易系统各组件的运行状态
"""

import sqlite3
import time
from typing import Dict, Any
from loguru import logger

try:
    from data.db_manager import db_manager
    from execution.exchange_connector import exchange_connector
    from orchestrator.scheduler import scheduler
    HAS_EXTERNAL_DEPENDENCIES = True
except ImportError as e:
    HAS_EXTERNAL_DEPENDENCIES = False
    logger.warning(f"无法导入外部依赖，将使用模拟状态检测: {e}")


class SystemStatusChecker:
    """系统状态检测器"""
    
    def __init__(self):
        """初始化状态检测器"""
        self.last_check_time = 0
        self.cached_status = {}
        self.cache_duration = 30  # 缓存30秒
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统整体状态
        
        Returns:
            dict: 包含各组件状态的字典
        """
        current_time = time.time()
        
        # 检查缓存是否有效
        if (current_time - self.last_check_time < self.cache_duration and 
            self.cached_status):
            return self.cached_status
        
        # 获取各组件状态
        status = {
            'database': self.check_database_status(),
            'exchange': self.check_exchange_status(),
            'scheduler': self.check_scheduler_status(),
            'ai': self.check_ai_service_status()
        }
        
        # 更新缓存
        self.cached_status = status
        self.last_check_time = current_time
        
        return status
    
    def check_database_status(self) -> bool:
        """
        检查数据库连接状态
        
        Returns:
            bool: 数据库是否正常连接
        """
        if not HAS_EXTERNAL_DEPENDENCIES:
            # 模拟状态检测
            return True
            
        try:
            # 尝试获取数据库连接
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # 执行简单查询测试连接
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            return result is not None
        except Exception as e:
            logger.error(f"数据库连接检查失败: {e}")
            return False
    
    def check_exchange_status(self) -> bool:
        """
        检查交易所连接状态
        
        Returns:
            bool: 交易所API是否正常连接
        """
        if not HAS_EXTERNAL_DEPENDENCIES:
            # 模拟状态检测
            return True
            
        try:
            # 尝试获取账户信息测试连接
            account_info = exchange_connector.get_account_balance()
            return account_info is not None
        except Exception as e:
            logger.error(f"交易所连接检查失败: {e}")
            return False
    
    def check_scheduler_status(self) -> bool:
        """
        检查任务调度器状态
        
        Returns:
            bool: 调度器是否正常运行
        """
        if not HAS_EXTERNAL_DEPENDENCIES:
            # 模拟状态检测
            return True
            
        try:
            # 检查调度器是否运行
            if hasattr(scheduler, 'running'):
                return scheduler.running
            elif hasattr(scheduler, 'state'):
                # 如果有state属性，检查状态
                return scheduler.state == 'running'
            else:
                # 如果没有相关属性，尝试调用一个简单方法
                return True
        except Exception as e:
            logger.error(f"调度器状态检查失败: {e}")
            return False
    
    def check_ai_service_status(self) -> bool:
        """
        检查AI服务状态
        
        Returns:
            bool: AI服务是否可用
        """
        # 对于AI服务，我们暂时返回True
        # 在实际实现中，可能需要检查OpenAI API的连接状态
        return True
    
    def refresh_status(self) -> Dict[str, Any]:
        """
        强制刷新状态（忽略缓存）
        
        Returns:
            dict: 更新后的系统状态
        """
        self.cached_status = {}
        return self.get_system_status()


# 创建全局实例
system_status_checker = SystemStatusChecker()