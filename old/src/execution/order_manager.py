"""
订单管理器
管理订单的完整生命周期，协调风控检查与订单提交
"""

import time
from typing import Optional, List, Dict, Any
from loguru import logger
from datetime import datetime

from data.models import Signal, Order, OrderSide, OrderType, OrderStatus, Position
from data.db_manager import db_manager
from .exchange_connector import exchange_connector
from .risk_controller import risk_controller
from config import get_config


class OrderManager:
    """订单管理器类"""
    
    def __init__(self):
        """初始化订单管理器"""
        self.config = get_config()
        logger.info("订单管理器初始化完成")
    
    def create_order_from_signal(
        self,
        signal: Signal,
        account_balance: float,
        positions: List[Position]
    ) -> Optional[Order]:
        """
        基于策略信号创建订单
        
        Args:
            signal: 策略信号
            account_balance: 账户余额（USDT）
            positions: 当前持仓列表
            
        Returns:
            Order: 创建的订单，失败返回 None
        """
        try:
            logger.info(f"开始处理交易信号: {signal.strategy_name} - {signal.symbol} {signal.signal_type.value}")
            
            # 1. 风控检查
            try:
                passed, reason = risk_controller.check_order_risk(
                    signal=signal,
                    account_balance=account_balance,
                    current_positions=positions
                )
                
                if not passed:
                    logger.warning(f"风控检查未通过: {reason}")
                    # 记录拒绝日志到数据库
                    self._log_rejected_signal(signal, reason)
                    return None
                
                logger.info(f"风控检查通过")
            except Exception as e:
                logger.error(f"风控检查异常: {e}")
                return None
            
            # 2. 计算订单数量
            try:
                quantity = self._calculate_order_quantity(
                    signal=signal,
                    account_balance=account_balance,
                    current_price=signal.price
                )
            except Exception as e:
                logger.error(f"计算订单数量异常: {e}")
                quantity = None
            
            if quantity is None or quantity <= 0:
                logger.error("订单数量计算失败")
                return None
            
            logger.info(f"计算订单数量: {quantity} (价格: {signal.price}, 置信度: {signal.confidence})")
            
            # 3. 创建订单对象
            order_side = OrderSide.BUY if signal.signal_type == SignalType.BUY else OrderSide.SELL
            
            order = Order(
                symbol=signal.symbol,
                side=order_side,
                order_type=OrderType.MARKET,  # 默认使用市价单
                quantity=quantity,
                price=signal.price,  # 预期价格
                status=OrderStatus.NEW,
                strategy_name=signal.strategy_name if hasattr(signal, 'strategy_name') else 'Unknown'
            )
            
            return order
            
        except Exception as e:
            logger.error(f"创建订单失败: {e}")
            return None
    
    def submit_order(self, order: Order) -> bool:
        """
        提交订单到交易所
        
        Args:
            order: 订单对象
            
        Returns:
            bool: 是否成功
        """
        try:
            logger.info(f"准备提交订单: {order.symbol} {order.side.value} {order.quantity}")
            
            # 确保交易所已连接
            if not exchange_connector.connected:
                if not exchange_connector.connect():
                    logger.error("交易所连接失败，无法提交订单")
                    return False
            
            # 根据订单类型提交
            if order.order_type == OrderType.MARKET:
                result = exchange_connector.place_market_order(
                    symbol=order.symbol,
                    side=order.side,
                    quantity=order.quantity
                )
            elif order.order_type == OrderType.LIMIT:
                if order.price is None:
                    logger.error("限价单缺少价格参数")
                    return False
                result = exchange_connector.place_limit_order(
                    symbol=order.symbol,
                    side=order.side,
                    price=order.price,
                    quantity=order.quantity
                )
            else:
                logger.error(f"不支持的订单类型: {order.order_type}")
                return False
            
            if result is None:
                logger.error("订单提交失败")
                return False
            
            # 更新订单信息
            order.order_id = result.order_id
            order.status = result.status
            order.executed_qty = result.executed_qty
            order.price = result.price  # 更新为实际成交价
            
            # 保存订单到数据库
            try:
                self._save_order_to_db(order)
            except Exception as e:
                logger.error(f"保存订单到数据库失败: {e}")
            
            logger.success(f"订单提交成功: {order.order_id} - {order.symbol} {order.side.value} {order.quantity}")
            return True
            
        except Exception as e:
            logger.error(f"提交订单失败: {e}")
            return False
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """
        撤销订单
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            bool: 是否成功
        """
        try:
            success = exchange_connector.cancel_order(symbol, order_id)
            
            if success:
                # 更新数据库中的订单状态
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "UPDATE trade_records SET status = ? WHERE order_id = ?",
                        (OrderStatus.CANCELED.value, order_id)
                    )
                    conn.commit()
                    logger.info(f"订单撤销成功: {order_id}")
                except Exception as e:
                    logger.error(f"更新数据库订单状态失败: {e}")
            
            return success
            
        except Exception as e:
            logger.error(f"撤销订单失败: {e}")
            return False
    
    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        查询订单信息
        
        Args:
            order_id: 订单ID
            
        Returns:
            dict: 订单信息
        """
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM trade_records 
                WHERE order_id = ?
                """,
                (order_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"查询订单失败: {e}")
            return None
    
    def get_recent_orders(self, symbol: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取最近订单
        
        Args:
            symbol: 交易对，None 表示所有交易对
            limit: 数量限制
            
        Returns:
            List[dict]: 订单列表
        """
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            if symbol:
                cursor.execute(
                    """
                    SELECT * FROM trade_records 
                    WHERE symbol = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (symbol, limit)
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM trade_records 
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (limit,)
                )
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"查询最近订单失败: {e}")
            return []
    
    def sync_order_status(self, symbol: str, order_id: str) -> Optional[OrderStatus]:
        """
        同步订单状态
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            OrderStatus: 订单状态
        """
        try:
            status = exchange_connector.get_order_status(symbol, order_id)
            
            if status:
                # 更新数据库
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "UPDATE trade_records SET status = ? WHERE order_id = ?",
                        (status.value, order_id)
                    )
                    conn.commit()
                    logger.debug(f"订单状态已同步: {order_id} - {status.value}")
                except Exception as e:
                    logger.error(f"更新数据库订单状态失败: {e}")
            
            return status
            
        except Exception as e:
            logger.error(f"同步订单状态失败: {e}")
            return None
    
    def _calculate_order_quantity(
        self,
        signal: Signal,
        account_balance: float,
        current_price: float
    ) -> Optional[float]:
        """
        计算订单数量
        
        Args:
            signal: 交易信号
            account_balance: 账户余额
            current_price: 当前价格
            
        Returns:
            float: 订单数量
        """
        try:
            # 获取单仓位限制
            max_position_percent = self.config['risk_control']['max_position_percent']
            
            # 计算可用资金
            available_funds = account_balance * max_position_percent
            
            # 计算基础数量
            base_quantity = available_funds / current_price
            
            # 根据信号置信度调整
            adjusted_quantity = base_quantity * signal.confidence
            
            # 根据交易对设置精度
            symbol = signal.symbol
            if symbol.endswith('USDT'):
                # USDT交易对通常精度为小数点后2-5位
                quantity = round(adjusted_quantity, 5)
            elif symbol.endswith('BTC'):
                # BTC交易对通常精度为小数点后5-8位
                quantity = round(adjusted_quantity, 8)
            else:
                # 默认精度
                quantity = round(adjusted_quantity, 5)
            
            # 检查最小订单量（以 BTC 为例，最小 0.00001）
            min_quantity = 0.00001
            if quantity < min_quantity:
                logger.warning(f"计算数量 {quantity} 小于最小订单量 {min_quantity}")
                return None
            
            logger.debug(f"订单数量计算: 可用资金={available_funds:.2f}, 基础数量={base_quantity:.6f}, 调整后={quantity:.6f}")
            
            return quantity
            
        except Exception as e:
            logger.error(f"计算订单数量失败: {e}")
            return None
    
    def _save_order_to_db(self, order: Order):
        """
        保存订单到数据库
        
        Args:
            order: 订单对象
        """
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO trade_records 
                (symbol, side, order_type, price, quantity, status, order_id, strategy_name, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order.symbol,
                    order.side.value,
                    order.order_type.value,
                    order.price,
                    order.quantity,
                    order.status.value,
                    order.order_id,
                    order.strategy_name,
                    order.created_time
                )
            )
            
            conn.commit()
            logger.debug(f"订单已保存到数据库: {order.order_id}")
            
        except Exception as e:
            logger.error(f"保存订单到数据库失败: {e}")
    
    def _log_rejected_signal(self, signal: Signal, reason: str):
        """
        记录被拒绝的信号
        
        Args:
            signal: 信号对象
            reason: 拒绝原因
        """
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO strategy_signals 
                (strategy_name, symbol, signal_type, price, timestamp, confidence, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal.strategy_name,
                    signal.symbol,
                    signal.signal_type.value,
                    signal.price,
                    signal.timestamp,
                    signal.confidence,
                    f"REJECTED: {reason}"
                )
            )
            
            conn.commit()
            logger.debug(f"已记录被拒绝的信号: {signal.symbol} - {reason}")
            
        except Exception as e:
            logger.error(f"记录拒绝信号失败: {e}")


# 全局实例
order_manager = OrderManager()
