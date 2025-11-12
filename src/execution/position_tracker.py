"""
持仓跟踪器
跟踪所有开仓持仓，实时监控止损触发，计算持仓盈亏
"""

import time
from typing import List, Optional, Dict, Any, Tuple
from loguru import logger
from datetime import datetime

from data.models import Position, Order, OrderSide, StopLossType
from data.db_manager import db_manager
from .exchange_connector import exchange_connector
from config import get_config


class PositionTracker:
    """持仓跟踪器类"""
    
    def __init__(self):
        """初始化持仓跟踪器"""
        self.config = get_config()
        self.position_config = self.config.get('position_tracking', {})
        self.risk_config = self.config.get('risk_control', {})
        
        self.monitor_interval = self.position_config.get('monitor_interval_seconds', 30)
        self.enable_auto_stop_loss = self.position_config.get('enable_auto_stop_loss', True)
        self.update_trailing_stop = self.position_config.get('update_trailing_stop', True)
        self.trailing_threshold = self.position_config.get('trailing_update_threshold', 0.005)
        
        logger.info(f"持仓跟踪器初始化 - 监控间隔: {self.monitor_interval}秒, 自动止损: {self.enable_auto_stop_loss}")
    
    def add_position(self, order: Order, stop_loss_price: float, stop_loss_type: StopLossType) -> bool:
        """
        添加新持仓
        
        Args:
            order: 开仓订单
            stop_loss_price: 止损价格
            stop_loss_type: 止损类型
        
        Returns:
            bool: 是否成功
        """
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # 检查是否已存在该交易对的持仓
            cursor.execute(
                "SELECT COUNT(*) as count FROM positions WHERE symbol = ? AND status = 'OPEN'",
                (order.symbol,)
            )
            result = cursor.fetchone()
            
            if result['count'] > 0:
                logger.warning(f"{order.symbol} 已存在开仓持仓")
                return False
            
            # 插入新持仓
            cursor.execute(
                """
                INSERT INTO positions 
                (symbol, entry_price, quantity, strategy_name, stop_loss_type, 
                 stop_loss_price, initial_stop_price, highest_price, entry_time, 
                 order_id, status, unrealized_pnl, unrealized_pnl_percent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order.symbol,
                    order.price,
                    order.quantity,
                    "Unknown",  # 策略名需要从 order 中传递
                    stop_loss_type.value,
                    stop_loss_price,
                    stop_loss_price,
                    order.price,  # 初始最高价为入场价
                    order.created_time,
                    order.order_id,
                    'OPEN',
                    0.0,
                    0.0
                )
            )
            
            conn.commit()
            logger.success(f"新持仓已添加: {order.symbol} @ {order.price}, 止损价: {stop_loss_price}")
            return True
            
        except Exception as e:
            logger.error(f"添加持仓失败: {e}")
            return False
    
    def close_position(self, position_id: int, close_price: float, reason: str = "Manual") -> bool:
        """
        平仓
        
        Args:
            position_id: 持仓ID
            close_price: 平仓价格
            reason: 平仓原因
        
        Returns:
            bool: 是否成功
        """
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # 获取持仓信息
            cursor.execute(
                "SELECT * FROM positions WHERE id = ?",
                (position_id,)
            )
            position_data = cursor.fetchone()
            
            if not position_data:
                logger.error(f"持仓不存在: {position_id}")
                return False
            
            position = dict(position_data)
            
            # 计算盈亏
            pnl = (close_price - position['entry_price']) * position['quantity']
            pnl_percent = (close_price / position['entry_price'] - 1) * 100
            
            # 更新持仓状态
            cursor.execute(
                """
                UPDATE positions 
                SET status = 'CLOSED', 
                    close_price = ?,
                    close_time = ?,
                    realized_pnl = ?,
                    realized_pnl_percent = ?,
                    close_reason = ?
                WHERE id = ?
                """,
                (
                    close_price,
                    int(time.time()),
                    pnl,
                    pnl_percent,
                    reason,
                    position_id
                )
            )
            
            conn.commit()
            
            logger.success(
                f"持仓已平仓: {position['symbol']} - "
                f"入场价: {position['entry_price']}, 平仓价: {close_price}, "
                f"盈亏: {pnl:.2f} ({pnl_percent:.2f}%), 原因: {reason}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"平仓失败: {e}")
            return False
    
    def update_position(self, position_id: int, current_price: float) -> bool:
        """
        更新持仓数据（浮动盈亏、移动止损等）
        
        Args:
            position_id: 持仓ID
            current_price: 当前价格
        
        Returns:
            bool: 是否成功
        """
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # 获取持仓信息
            cursor.execute(
                "SELECT * FROM positions WHERE id = ? AND status = 'OPEN'",
                (position_id,)
            )
            position_data = cursor.fetchone()
            
            if not position_data:
                return False
            
            position = dict(position_data)
            
            # 计算浮动盈亏
            unrealized_pnl = (current_price - position['entry_price']) * position['quantity']
            unrealized_pnl_percent = (current_price / position['entry_price'] - 1) * 100
            
            # 更新最高价
            highest_price = max(position['highest_price'], current_price)
            
            # 计算新的止损价（如果是移动止损）
            new_stop_loss = position['stop_loss_price']
            
            if self.update_trailing_stop and position['stop_loss_type'] == StopLossType.TRAILING.value:
                # 检查是否需要更新移动止损
                if current_price > position['entry_price']:  # 只在盈利时更新
                    price_increase = (current_price - position['highest_price']) / position['highest_price']
                    
                    if price_increase >= self.trailing_threshold:
                        # 更新移动止损价
                        trailing_percent = self.risk_config.get('trailing_stop_percent', 0.02)
                        new_stop_loss = current_price * (1 - trailing_percent)
                        
                        # 确保止损价只升不降
                        if new_stop_loss > position['stop_loss_price']:
                            logger.info(
                                f"更新移动止损: {position['symbol']} - "
                                f"旧止损: {position['stop_loss_price']:.2f}, "
                                f"新止损: {new_stop_loss:.2f}"
                            )
            
            # 更新数据库
            cursor.execute(
                """
                UPDATE positions 
                SET unrealized_pnl = ?,
                    unrealized_pnl_percent = ?,
                    highest_price = ?,
                    stop_loss_price = ?,
                    last_update_time = ?
                WHERE id = ?
                """,
                (
                    unrealized_pnl,
                    unrealized_pnl_percent,
                    highest_price,
                    new_stop_loss,
                    int(time.time()),
                    position_id
                )
            )
            
            conn.commit()
            
            logger.debug(
                f"持仓已更新: {position['symbol']} - "
                f"当前价: {current_price}, 浮盈: {unrealized_pnl:.2f} ({unrealized_pnl_percent:.2f}%)"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"更新持仓失败: {e}")
            return False
    
    def get_all_positions(self, status: str = 'OPEN') -> List[Position]:
        """
        获取所有持仓
        
        Args:
            status: 持仓状态 ('OPEN' / 'CLOSED')
        
        Returns:
            List[Position]: 持仓列表
        """
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM positions WHERE status = ? ORDER BY entry_time DESC",
                (status,)
            )
            
            rows = cursor.fetchall()
            positions = []
            
            for row in rows:
                data = dict(row)
                position = Position(
                    symbol=data['symbol'],
                    entry_price=data['entry_price'],
                    quantity=data['quantity'],
                    strategy_name=data['strategy_name'],
                    stop_loss_type=StopLossType(data['stop_loss_type']),
                    stop_loss_price=data['stop_loss_price'],
                    initial_stop_price=data['initial_stop_price'],
                    highest_price=data['highest_price'],
                    entry_time=data['entry_time'],
                    unrealized_pnl=data.get('unrealized_pnl', 0.0),
                    unrealized_pnl_percent=data.get('unrealized_pnl_percent', 0.0)
                )
                positions.append(position)
            
            return positions
            
        except Exception as e:
            logger.error(f"获取持仓列表失败: {e}")
            return []
    
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取指定交易对的持仓
        
        Args:
            symbol: 交易对
        
        Returns:
            dict: 持仓信息
        """
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM positions WHERE symbol = ? AND status = 'OPEN' LIMIT 1",
                (symbol,)
            )
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            return None
    
    def check_stop_loss(self) -> List[Tuple[int, str, str]]:
        """
        检查所有持仓的止损触发情况
        
        Returns:
            List[Tuple]: 需要止损的持仓列表 [(position_id, symbol, reason)]
        """
        triggered_positions = []
        
        try:
            # 获取所有开仓持仓
            positions = self.get_all_positions(status='OPEN')
            
            if not positions:
                logger.debug("当前无开仓持仓")
                return triggered_positions
            
            logger.debug(f"检查 {len(positions)} 个持仓的止损条件")
            
            # 获取当前价格
            current_prices = {}
            for position in positions:
                if position.symbol not in current_prices:
                    price = exchange_connector.get_current_price(position.symbol)
                    if price:
                        current_prices[position.symbol] = price
            
            # 检查每个持仓
            for position in positions:
                symbol = position.symbol
                if symbol not in current_prices:
                    logger.warning(f"无法获取 {symbol} 的当前价格，跳过止损检查")
                    continue
                
                current_price = current_prices[symbol]
                
                # 先更新持仓数据
                position_data = self.get_position(symbol)
                if position_data:
                    self.update_position(position_data['id'], current_price)
                    
                    # 重新获取更新后的止损价
                    updated_position = self.get_position(symbol)
                    if updated_position:
                        stop_loss_price = updated_position['stop_loss_price']
                        
                        # 检查是否触发止损
                        if self._check_stop_loss_trigger(
                            position, 
                            current_price, 
                            stop_loss_price
                        ):
                            reason = self._get_stop_loss_reason(position, current_price)
                            triggered_positions.append((
                                updated_position['id'], 
                                symbol, 
                                reason
                            ))
                            
                            logger.warning(
                                f"止损触发: {symbol} - "
                                f"当前价: {current_price}, 止损价: {stop_loss_price}, "
                                f"原因: {reason}"
                            )
            
            return triggered_positions
            
        except Exception as e:
            logger.error(f"检查止损失败: {e}")
            return triggered_positions
    
    def calculate_pnl(self, position: Position, current_price: float) -> float:
        """
        计算浮动盈亏
        
        Args:
            position: 持仓对象
            current_price: 当前价格
        
        Returns:
            float: 浮动盈亏金额
        """
        return (current_price - position.entry_price) * position.quantity
    
    def _check_stop_loss_trigger(
        self, 
        position: Position, 
        current_price: float,
        stop_loss_price: float
    ) -> bool:
        """
        检查止损是否触发
        
        Args:
            position: 持仓对象
            current_price: 当前价格
            stop_loss_price: 止损价格
        
        Returns:
            bool: 是否触发止损
        """
        # 固定百分比、关键点位、ATR、移动止损
        if position.stop_loss_type in [
            StopLossType.FIXED_PERCENT,
            StopLossType.KEY_LEVEL,
            StopLossType.ATR_BASED,
            StopLossType.TRAILING
        ]:
            return current_price <= stop_loss_price
        
        # 时间止损
        elif position.stop_loss_type == StopLossType.TIME_BASED:
            current_time = int(time.time())
            holding_days = (current_time - position.entry_time) / 86400  # 转换为天数
            max_holding_days = self.risk_config.get('max_holding_days', 30)
            return holding_days >= max_holding_days
        
        return False
    
    def _get_stop_loss_reason(self, position: Position, current_price: float) -> str:
        """
        获取止损原因描述
        
        Args:
            position: 持仓对象
            current_price: 当前价格
        
        Returns:
            str: 止损原因
        """
        if position.stop_loss_type == StopLossType.FIXED_PERCENT:
            loss_percent = (current_price / position.entry_price - 1) * 100
            return f"固定百分比止损 ({loss_percent:.2f}%)"
        
        elif position.stop_loss_type == StopLossType.KEY_LEVEL:
            return f"跌破关键支撑位 {position.stop_loss_price}"
        
        elif position.stop_loss_type == StopLossType.ATR_BASED:
            return "ATR 动态止损触发"
        
        elif position.stop_loss_type == StopLossType.TRAILING:
            return f"移动止损触发 (最高价: {position.highest_price})"
        
        elif position.stop_loss_type == StopLossType.TIME_BASED:
            holding_days = (int(time.time()) - position.entry_time) / 86400
            return f"时间止损 (持仓 {holding_days:.1f} 天)"
        
        elif position.stop_loss_type == StopLossType.MANUAL:
            return "手动止损"
        
        return "未知原因"


# 全局实例
position_tracker = PositionTracker()
