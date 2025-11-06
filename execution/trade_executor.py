"""
交易执行器
统一管理从策略信号到订单执行的完整流程
"""

import threading
import time
from typing import List, Optional, Dict, Any
from queue import Queue, PriorityQueue
from dataclasses import dataclass, field
from loguru import logger
from datetime import datetime

from data.models import Signal, Order, Position, SignalType
from data.db_manager import db_manager
from execution.order_manager import order_manager
from execution.position_tracker import position_tracker
from execution.exchange_connector import exchange_connector
from execution.risk_controller import risk_controller
from config import get_config


@dataclass(order=True)
class PrioritizedSignal:
    """带优先级的信号（用于优先队列）"""
    priority: float = field(compare=True)  # 优先级（置信度，越高越优先）
    signal: Signal = field(compare=False)
    timestamp: float = field(default_factory=time.time, compare=False)


class TradeExecutor:
    """交易执行器类"""
    
    def __init__(self):
        """初始化交易执行器"""
        self.config = get_config()
        
        # 信号队列（优先队列，按置信度排序）
        self.signal_queue = PriorityQueue()
        
        # 处理中的订单
        self.processing_orders: Dict[str, Order] = {}
        
        # 执行器状态
        self.running = False
        self.executor_thread: Optional[threading.Thread] = None
        
        # 统计信息
        self.stats = {
            'signals_received': 0,
            'signals_processed': 0,
            'orders_submitted': 0,
            'orders_success': 0,
            'orders_failed': 0,
            'risk_rejected': 0
        }
        
        logger.info("交易执行器初始化完成")
    
    def start(self):
        """启动交易执行器"""
        if self.running:
            logger.warning("交易执行器已在运行")
            return
        
        self.running = True
        self.executor_thread = threading.Thread(target=self._execute_loop, daemon=True)
        self.executor_thread.start()
        logger.success("交易执行器已启动")
    
    def stop(self):
        """停止交易执行器"""
        if not self.running:
            return
        
        self.running = False
        if self.executor_thread:
            self.executor_thread.join(timeout=5)
        
        logger.info(f"交易执行器已停止 - 统计: {self.stats}")
    
    def submit_signal(self, signal: Signal) -> bool:
        """
        提交交易信号到队列
        
        Args:
            signal: 策略信号
        
        Returns:
            bool: 是否成功加入队列
        """
        try:
            # 创建优先级信号（优先级 = 置信度，越高越先处理）
            prioritized = PrioritizedSignal(
                priority=-signal.confidence,  # 负值，因为PriorityQueue是最小堆
                signal=signal
            )
            
            self.signal_queue.put(prioritized)
            self.stats['signals_received'] += 1
            
            logger.info(
                f"信号已加入队列: {signal.symbol} {signal.signal_type.value} "
                f"@ {signal.price:.2f} (置信度: {signal.confidence:.2f})"
            )
            return True
            
        except Exception as e:
            logger.error(f"提交信号失败: {e}")
            return False
    
    def submit_signals_batch(self, signals: List[Signal]) -> int:
        """
        批量提交信号
        
        Args:
            signals: 信号列表
        
        Returns:
            int: 成功加入队列的数量
        """
        success_count = 0
        for signal in signals:
            if self.submit_signal(signal):
                success_count += 1
        
        logger.info(f"批量提交信号: {success_count}/{len(signals)} 成功")
        return success_count
    
    def _execute_loop(self):
        """执行循环（在后台线程运行）"""
        logger.info("交易执行循环已启动")
        
        while self.running:
            try:
                # 获取优先级最高的信号（阻塞等待，超时1秒）
                prioritized_signal = self.signal_queue.get(timeout=1)
                signal = prioritized_signal.signal
                
                logger.info(
                    f"处理信号: {signal.symbol} {signal.signal_type.value} "
                    f"(置信度: {signal.confidence:.2f})"
                )
                
                # 执行信号
                self._execute_signal(signal)
                self.stats['signals_processed'] += 1
                
            except Exception as e:
                if "Empty" not in str(e):  # 忽略队列空的正常超时
                    logger.error(f"执行循环错误: {e}")
            
            time.sleep(0.1)  # 短暂休眠，避免CPU占用过高
        
        logger.info("交易执行循环已停止")
    
    def _execute_signal(self, signal: Signal):
        """
        执行单个信号
        
        Args:
            signal: 交易信号
        """
        try:
            # 1. 获取账户信息
            account_balance = self._get_account_balance()
            if account_balance is None:
                logger.error("无法获取账户余额，跳过信号执行")
                return
            
            # 2. 获取当前持仓
            positions = position_tracker.get_all_positions(status='OPEN')
            
            # 3. 创建订单
            order = order_manager.create_order_from_signal(
                signal=signal,
                account_balance=account_balance,
                positions=positions
            )
            
            if order is None:
                logger.warning(f"订单创建失败，信号被拒绝: {signal.symbol}")
                self.stats['risk_rejected'] += 1
                return
            
            # 4. 提交订单
            self.stats['orders_submitted'] += 1
            success = order_manager.submit_order(order)
            
            if success:
                self.stats['orders_success'] += 1
                logger.success(f"订单执行成功: {order.order_id}")
                
                # 5. 如果是买入订单，注册持仓监控
                if signal.signal_type == SignalType.BUY and order.order_id:
                    # 计算止损价（从风控模块获取）
                    stop_loss_price, stop_loss_type = risk_controller.calculate_stop_loss(
                        entry_price=order.price,
                        stop_loss_config=self.config.get('risk_control', {}),
                        symbol=signal.symbol
                    )
                    
                    # 添加持仓跟踪
                    position_tracker.add_position(
                        order=order,
                        stop_loss_price=stop_loss_price,
                        stop_loss_type=stop_loss_type
                    )
            else:
                self.stats['orders_failed'] += 1
                logger.error(f"订单执行失败: {signal.symbol}")
                
        except Exception as e:
            logger.error(f"执行信号失败: {e}")
            self.stats['orders_failed'] += 1
    
    def _get_account_balance(self) -> Optional[float]:
        """
        获取账户USDT余额
        
        Returns:
            float: USDT余额
        """
        try:
            balance_info = exchange_connector.get_account_balance()
            
            if 'USDT' in balance_info:
                usdt_balance = balance_info['USDT']['free']
                logger.debug(f"账户USDT余额: {usdt_balance:.2f}")
                return usdt_balance
            else:
                # 如果交易所未连接，返回模拟余额
                logger.warning("未获取到USDT余额，使用默认值")
                return 10000.0
                
        except Exception as e:
            logger.error(f"获取账户余额失败: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取执行器统计信息"""
        return {
            **self.stats,
            'queue_size': self.signal_queue.qsize(),
            'running': self.running
        }
    
    def clear_queue(self):
        """清空信号队列"""
        while not self.signal_queue.empty():
            try:
                self.signal_queue.get_nowait()
            except:
                break
        logger.info("信号队列已清空")


# 全局实例
trade_executor = TradeExecutor()
