"""
任务状态管理功能演示脚本
"""

import time
import os
from pathlib import Path

from utils.state_manager import state_manager
from utils.task_logger import task_logger
from utils.signal_queue_manager import signal_queue_manager
from utils.recovery_manager import recovery_manager
from data.db_manager import db_manager
from data.models import Signal, SignalType


def demo_system_state_management():
    """演示系统状态管理功能"""
    print("=== 系统状态管理演示 ===")
    
    # 初始化数据库
    db_manager.init_database()
    
    # 创建系统实例
    instance_id = state_manager.create_instance('demo')
    task_logger.set_instance_id(instance_id)
    print(f"创建系统实例: {instance_id}")
    
    # 更新心跳
    state_manager.update_heartbeat()
    print("更新心跳完成")
    
    # 检查上次实例
    last_instance = state_manager.get_last_instance()
    print(f"上次实例: {last_instance['instance_id']}")
    
    # 标记停止
    state_manager.mark_stopped('demo_complete')
    print("标记系统停止完成")


def demo_task_logging():
    """演示任务日志记录功能"""
    print("\n=== 任务日志记录演示 ===")
    
    # 记录任务开始
    task_id = task_logger.log_task_start('demo_task', 'demo', {'param': 'value'})
    print(f"任务开始，ID: {task_id}")
    
    # 模拟任务执行
    time.sleep(1)
    
    # 记录任务结束
    task_logger.log_task_end(task_id, {'result': 'success'}, None)
    print("任务结束")
    
    # 查询任务历史
    history = task_logger.get_task_history('demo_task')
    print(f"任务历史: {len(history)} 条记录")
    
    # 获取任务统计
    stats = task_logger.get_task_statistics()
    print(f"任务统计: {stats}")


def demo_signal_queue_management():
    """演示信号队列管理功能"""
    print("\n=== 信号队列管理演示 ===")
    
    # 创建测试信号
    signal = Signal(
        strategy_name='demo_strategy',
        symbol='BTCUSDT',
        signal_type=SignalType.BUY,
        price=50000.0,
        timestamp=int(time.time()),
        confidence=0.85
    )
    
    # 信号入队
    signal_id = signal_queue_manager.enqueue_signal(signal)
    print(f"信号入队: {signal_id}")
    
    # 获取队列状态
    status = signal_queue_manager.get_queue_status()
    print(f"队列状态: {status}")
    
    # 加载待处理信号
    pending_signals = signal_queue_manager.dequeue_signals()
    print(f"加载待处理信号: {len(pending_signals)} 个")
    
    # 标记信号完成
    signal_queue_manager.mark_signal_completed(signal_id, 'demo_order_id')
    print("标记信号完成")
    
    # 检查状态更新
    status = signal_queue_manager.get_queue_status()
    print(f"更新后队列状态: {status}")


def demo_recovery_management():
    """演示恢复管理功能"""
    print("\n=== 恢复管理演示 ===")
    
    # 检查是否需要恢复
    needs_recovery = recovery_manager.check_recovery_needed()
    print(f"是否需要恢复: {needs_recovery}")
    
    # 标记系统崩溃
    state_manager.mark_crashed('demo_crash')
    print("标记系统崩溃")
    
    # 检查是否需要恢复
    needs_recovery = recovery_manager.check_recovery_needed()
    print(f"崩溃后是否需要恢复: {needs_recovery}")
    
    # 执行恢复
    recovery_result = recovery_manager.execute_recovery()
    print(f"恢复执行结果: {recovery_result}")


def main():
    """主函数"""
    print("任务状态管理功能演示")
    print("=" * 50)
    
    try:
        demo_system_state_management()
        demo_task_logging()
        demo_signal_queue_management()
        demo_recovery_management()
        
        print("\n所有演示完成！")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        raise


if __name__ == '__main__':
    main()