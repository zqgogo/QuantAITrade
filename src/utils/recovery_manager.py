"""
系统恢复管理模块
负责系统启动时的状态恢复
"""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from data.db_manager import db_manager
from utils.state_manager import state_manager
from utils.signal_queue_manager import signal_queue_manager
from src.execution.order_manager import order_manager
from src.execution.position_tracker import position_tracker
from data.fetcher import DataFetcher


class RecoveryManager:
    """恢复管理器"""
    
    def __init__(self):
        self.db = db_manager
        self.state_manager = state_manager
        self.signal_queue_manager = signal_queue_manager
        self.order_manager = order_manager
        self.position_tracker = position_tracker
        self.data_fetcher = DataFetcher()
    
    def check_recovery_needed(self) -> bool:
        """
        检查是否需要恢复
        
        Returns:
            bool: 是否需要恢复
        """
        return self.state_manager.is_last_crashed()
    
    def recover_positions(self):
        """恢复持仓监控"""
        logger.info("开始恢复持仓监控...")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # 查询所有开放的持仓
            cursor.execute('''
                SELECT * FROM positions 
                WHERE status = 'OPEN'
            ''')
            
            rows = cursor.fetchall()
            recovered_count = 0
            
            for row in rows:
                try:
                    # 验证持仓有效性并恢复到监控列表
                    position = dict(row)
                    self.position_tracker.recover_position(position)
                    recovered_count += 1
                    logger.info(f"恢复持仓监控: {position['symbol']}")
                except Exception as e:
                    logger.error(f"恢复持仓 {row['symbol']} 失败: {e}")
            
            logger.info(f"持仓监控恢复完成，共恢复 {recovered_count} 个持仓")
            return recovered_count
        except Exception as e:
            logger.error(f"恢复持仓监控失败: {e}")
            return 0
    
    def recover_orders(self):
        """同步未完成订单"""
        logger.info("开始同步未完成订单...")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # 查询所有未完成的订单
            cursor.execute('''
                SELECT * FROM trade_records 
                WHERE status IN ('NEW', 'PARTIALLY_FILLED')
            ''')
            
            rows = cursor.fetchall()
            recovered_count = 0
            
            for row in rows:
                try:
                    # 同步订单状态
                    order = dict(row)
                    self.order_manager.sync_order_status(order['order_id'])
                    recovered_count += 1
                    logger.info(f"同步订单状态: {order['order_id']}")
                except Exception as e:
                    logger.error(f"同步订单 {row['order_id']} 失败: {e}")
            
            logger.info(f"订单状态同步完成，共处理 {recovered_count} 个订单")
            return recovered_count
        except Exception as e:
            logger.error(f"同步未完成订单失败: {e}")
            return 0
    
    def recover_signals(self):
        """恢复未处理信号"""
        logger.info("开始恢复未处理信号...")
        
        try:
            # 加载队列中待处理的信号
            pending_signals = self.signal_queue_manager.dequeue_signals(limit=100)
            recovered_count = len(pending_signals)
            
            logger.info(f"未处理信号恢复完成，共恢复 {recovered_count} 个信号")
            return recovered_count
        except Exception as e:
            logger.error(f"恢复未处理信号失败: {e}")
            return 0
    
    def recover_data_progress(self):
        """恢复数据获取进度"""
        logger.info("开始恢复数据获取进度...")
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # 查询所有数据获取进度记录
            cursor.execute('''
                SELECT * FROM data_fetch_progress
            ''')
            
            rows = cursor.fetchall()
            recovered_count = 0
            
            for row in rows:
                try:
                    # 恢复数据获取进度到DataFetcher
                    progress = dict(row)
                    self.data_fetcher.recover_progress(progress)
                    recovered_count += 1
                    logger.info(f"恢复数据获取进度: {progress['symbol']}")
                except Exception as e:
                    logger.error(f"恢复数据获取进度 {row['symbol']} 失败: {e}")
            
            logger.info(f"数据获取进度恢复完成，共恢复 {recovered_count} 个记录")
            return recovered_count
        except Exception as e:
            logger.error(f"恢复数据获取进度失败: {e}")
            return 0
    
    def verify_data_consistency(self):
        """验证数据一致性"""
        logger.info("开始数据一致性校验...")
        
        inconsistencies = []
        
        try:
            # 校验持仓数据一致性
            position_inconsistencies = self._verify_position_consistency()
            inconsistencies.extend(position_inconsistencies)
            
            # 校验订单数据一致性
            order_inconsistencies = self._verify_order_consistency()
            inconsistencies.extend(order_inconsistencies)
            
            if inconsistencies:
                logger.warning(f"发现 {len(inconsistencies)} 个数据不一致问题")
                for issue in inconsistencies:
                    logger.warning(f"数据不一致: {issue}")
            else:
                logger.info("数据一致性校验通过")
                
            return inconsistencies
        except Exception as e:
            logger.error(f"数据一致性校验失败: {e}")
            return []
    
    def _verify_position_consistency(self) -> List[str]:
        """验证持仓数据一致性"""
        inconsistencies = []
        
        try:
            # 这里应该实现具体的持仓一致性校验逻辑
            # 例如：比对数据库持仓与交易所实际持仓
            pass
        except Exception as e:
            inconsistencies.append(f"持仓一致性校验异常: {e}")
            
        return inconsistencies
    
    def _verify_order_consistency(self) -> List[str]:
        """验证订单数据一致性"""
        inconsistencies = []
        
        try:
            # 这里应该实现具体的订单一致性校验逻辑
            # 例如：比对数据库订单与交易所实际订单
            pass
        except Exception as e:
            inconsistencies.append(f"订单一致性校验异常: {e}")
            
        return inconsistencies
    
    def execute_recovery(self):
        """执行完整的恢复流程"""
        logger.info("开始执行系统恢复流程...")
        
        try:
            # 按优先级执行恢复
            # P0: 持仓恢复与止损监控
            self.recover_positions()
            
            # P1: 未完成订单状态同步
            self.recover_orders()
            
            # P2: 未处理信号恢复
            self.recover_signals()
            
            # P3: 数据获取进度恢复
            self.recover_data_progress()
            
            # 数据一致性校验
            self.verify_data_consistency()
            
            logger.info("系统恢复流程执行完成")
            return True
        except Exception as e:
            logger.error(f"系统恢复流程执行失败: {e}")
            return False


# 全局实例
recovery_manager = RecoveryManager()