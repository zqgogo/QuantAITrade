"""
任务状态管理功能测试
"""

import unittest
import time
import sqlite3
import os
from datetime import datetime
from pathlib import Path

from utils.state_manager import state_manager
from utils.task_logger import task_logger
from utils.signal_queue_manager import signal_queue_manager
from utils.recovery_manager import recovery_manager
from data.db_manager import db_manager
from data.models import Signal, SignalType


class TestTaskStateManagement(unittest.TestCase):
    """任务状态管理测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 删除测试数据库文件（如果存在）
        db_path = Path("data/test_kline.db")
        if db_path.exists():
            db_path.unlink()
        
        # 设置测试数据库路径
        os.environ['DATABASE_PATH'] = str(db_path)
        
        # 重新初始化数据库管理器
        db_manager.db_path = db_path
        db_manager._connection = None
        
        # 初始化数据库
        db_manager.init_database()
        
        # 创建系统实例
        self.instance_id = state_manager.create_instance('test')
        task_logger.set_instance_id(self.instance_id)
    
    def tearDown(self):
        """测试后清理"""
        # 清理数据库连接
        db_manager.close()
        
        # 删除测试数据库文件
        db_path = Path("data/test_kline.db")
        if db_path.exists():
            db_path.unlink()
    
    def test_system_state_management(self):
        """测试系统状态管理"""
        # 创建实例
        self.assertIsNotNone(self.instance_id)
        self.assertEqual(state_manager.current_instance_id, self.instance_id)
        
        # 更新心跳
        state_manager.update_heartbeat()
        
        # 检查上次实例
        last_instance = state_manager.get_last_instance()
        self.assertIsNotNone(last_instance)
        self.assertEqual(last_instance['instance_id'], self.instance_id)
        self.assertEqual(last_instance['status'], 'running')
        
        # 标记停止
        state_manager.mark_stopped('test')
        
        # 检查状态更新
        last_instance = state_manager.get_last_instance()
        self.assertEqual(last_instance['status'], 'stopped')
        self.assertEqual(last_instance['stop_reason'], 'test')
    
    def test_task_logging(self):
        """测试任务日志记录"""
        # 记录任务开始
        task_id = task_logger.log_task_start('test_task', 'test', {'param': 'value'})
        self.assertIsNotNone(task_id)
        
        # 记录任务结束
        task_logger.log_task_end(task_id, {'result': 'success'}, None)
        
        # 查询任务历史
        history = task_logger.get_task_history('test_task')
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['status'], 'success')
        
        # 获取任务统计
        stats = task_logger.get_task_statistics()
        self.assertIn('test_task', stats)
        self.assertIn('success', stats['test_task'])
    
    def test_signal_queue_management(self):
        """测试信号队列管理"""
        # 创建测试信号
        signal = Signal(
            strategy_name='test_strategy',
            symbol='BTCUSDT',
            signal_type=SignalType.BUY,
            price=50000.0,
            timestamp=int(time.time()),
            confidence=0.85
        )
        
        # 信号入队
        signal_id = signal_queue_manager.enqueue_signal(signal)
        self.assertIsNotNone(signal_id)
        
        # 获取队列状态
        status = signal_queue_manager.get_queue_status()
        self.assertIn('pending', status)
        self.assertGreater(status['pending'], 0)
        
        # 加载待处理信号
        pending_signals = signal_queue_manager.dequeue_signals()
        self.assertEqual(len(pending_signals), 1)
        self.assertEqual(pending_signals[0]['signal_id'], signal_id)
        
        # 标记信号完成
        signal_queue_manager.mark_signal_completed(signal_id, 'test_order_id')
        
        # 检查状态更新
        status = signal_queue_manager.get_queue_status()
        self.assertIn('completed', status)
        self.assertGreater(status['completed'], 0)
    
    def test_recovery_management(self):
        """测试恢复管理"""
        # 检查是否需要恢复
        needs_recovery = recovery_manager.check_recovery_needed()
        self.assertFalse(needs_recovery)  # 正常关闭不需要恢复
        
        # 标记系统崩溃
        state_manager.mark_crashed('test crash')
        
        # 检查是否需要恢复
        needs_recovery = recovery_manager.check_recovery_needed()
        self.assertTrue(needs_recovery)
        
        # 执行恢复（应该不会出错）
        recovery_result = recovery_manager.execute_recovery()
        self.assertTrue(recovery_result)


if __name__ == '__main__':
    unittest.main()