"""
风险控制模块
实现多层风控机制和灵活的止损系统
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from loguru import logger

from config import get_config
from data.models import Signal, TradeRecord, Position, StopLossType, OrderSide
from data.db_manager import db_manager


class RiskController:
    """风险控制器类"""
    
    def __init__(self):
        """初始化风控模块"""
        self.config = get_config()
        self.risk_config = self.config['risk_control']
        logger.info("风控模块初始化完成")
    
    def check_order_risk(
        self,
        signal: Signal,
        account_balance: float,
        current_positions: List[Position]
    ) -> tuple[bool, str]:
        """
        检查订单风险（多层风控）
        
        Args:
            signal: 交易信号
            account_balance: 账户余额
            current_positions: 当前持仓列表
            
        Returns:
            (是否通过风控, 拒绝原因)
        """
        try:
            # 1. 检查账户余额
            if account_balance <= 0:
                return False, "账户余额不足"
            
            # 2. 检查单仓位限制
            try:
                max_position_percent = self.risk_config.get('max_position_percent', 0.03)
                max_position_value = account_balance * max_position_percent
                
                # 估算订单金额（假设买入1个单位）
                order_value = signal.price
                
                if order_value > max_position_value:
                    return False, f"超过单仓位限制({max_position_percent*100}%): {order_value:.2f} > {max_position_value:.2f}"
            except Exception as e:
                logger.warning(f"单仓位限制检查异常: {e}")
            
            # 3. 检查总仓位限制
            try:
                max_total_position = self.risk_config.get('max_total_position', 0.8)
                total_position_value = sum(p.quantity * p.entry_price for p in current_positions)
                
                if (total_position_value + order_value) > (account_balance * max_total_position):
                    return False, f"超过总仓位限制({max_total_position*100}%)"
            except Exception as e:
                logger.warning(f"总仓位限制检查异常: {e}")
            
            # 4. 检查每日交易次数
            try:
                max_daily_trades = self.risk_config.get('max_daily_trades', 10)
                today_trades_count = self._get_today_trades_count()
                
                if today_trades_count >= max_daily_trades:
                    return False, f"超过每日交易次数限制({max_daily_trades}次)"
            except Exception as e:
                logger.warning(f"每日交易次数检查异常: {e}")
            
            # 5. 检查价格偏差
            try:
                max_price_deviation = self.risk_config.get('max_price_deviation', 0.01)
                # TODO: 获取市场价格并比较
                # current_market_price = ...
                # if abs(signal.price - current_market_price) / current_market_price > max_price_deviation:
                #     return False, f"订单价格与市价偏差过大"
            except Exception as e:
                logger.warning(f"价格偏差检查异常: {e}")
            
            # 6. 检查是否已有相同交易对的持仓
            try:
                for pos in current_positions:
                    # 检查交易对和策略名称
                    if pos.symbol == signal.symbol:
                        # 如果是相同策略，拒绝
                        if hasattr(signal, 'strategy_name') and pos.strategy_name == signal.strategy_name:
                            return False, f"已有相同策略的{signal.symbol}持仓"
                        # 如果是不同策略但相同交易对，可以考虑是否允许
            except Exception as e:
                logger.warning(f"持仓检查异常: {e}")
            
            logger.info(f"订单风控检查通过: {signal.symbol} @ {signal.price}")
            return True, "通过"
        except Exception as e:
            logger.error(f"风控检查异常: {e}")
            return False, f"风控检查异常: {e}"
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        stop_loss_config: Dict[str, Any],
        symbol: str
    ) -> tuple[float, StopLossType]:
        """
        计算止损价格
        
        Args:
            entry_price: 入场价格
            stop_loss_config: 止损配置
            symbol: 交易对
            
        Returns:
            (止损价格, 止损类型)
        """
        try:
            stop_type = stop_loss_config.get('type', 'fixed_percent')
            
            if stop_type == 'fixed_percent':
                # 固定百分比止损
                percent = stop_loss_config.get('stop_loss_percent', 
                                              self.risk_config['stop_loss_percent'])
                stop_price = entry_price * (1 - percent)
                logger.info(f"固定止损: {stop_price:.2f} ({percent*100}%)")
                return stop_price, StopLossType.FIXED_PERCENT
                
            elif stop_type == 'key_level':
                # 关键点位止损
                # TODO: 从历史数据中计算支撑位
                # 暂时使用默认3%
                stop_price = entry_price * 0.97
                logger.info(f"关键点位止损: {stop_price:.2f}")
                return stop_price, StopLossType.KEY_LEVEL
                
            elif stop_type == 'atr_based':
                # ATR动态止损
                # TODO: 计算ATR值
                # 暂时使用默认3%
                stop_price = entry_price * 0.97
                logger.info(f"ATR动态止损: {stop_price:.2f}")
                return stop_price, StopLossType.ATR_BASED
                
            elif stop_type == 'trailing':
                # 移动止损（初始设置为固定止损，后续动态调整）
                percent = self.risk_config.get('trailing_stop_percent', 0.02)
                stop_price = entry_price * (1 - percent)
                logger.info(f"移动止损（初始）: {stop_price:.2f}")
                return stop_price, StopLossType.TRAILING
                
            else:
                # 默认3%固定止损
                stop_price = entry_price * 0.97
                logger.warning(f"未知止损类型: {stop_type}, 使用默认3%")
                return stop_price, StopLossType.FIXED_PERCENT
        except Exception as e:
            logger.error(f"计算止损价格失败: {e}")
            # 返回默认止损价格
            stop_price = entry_price * 0.97
            return stop_price, StopLossType.FIXED_PERCENT
    
    def check_stop_loss_trigger(
        self,
        position: Position,
        current_price: float
    ) -> bool:
        """
        检查是否触发止损
        
        Args:
            position: 持仓信息
            current_price: 当前价格
            
        Returns:
            是否触发止损
        """
        try:
            # 1. 价格止损检查
            if current_price <= position.stop_loss_price:
                logger.warning(f"触发止损: {position.symbol}, "
                             f"当前价{current_price:.2f} <= 止损价{position.stop_loss_price:.2f}")
                return True
            
            # 2. 移动止损更新
            if position.stop_loss_type == StopLossType.TRAILING:
                if current_price > position.highest_price:
                    # 更新最高价
                    position.highest_price = current_price
                    # 计算新的止损价
                    trailing_percent = self.risk_config.get('trailing_stop_percent', 0.02)
                    new_stop_price = current_price * (1 - trailing_percent)
                    # 止损价只能上移，不能下移
                    if new_stop_price > position.stop_loss_price:
                        logger.info(f"移动止损更新: {position.symbol}, "
                                  f"{position.stop_loss_price:.2f} -> {new_stop_price:.2f}")
                        position.stop_loss_price = new_stop_price
            
            # 3. 时间止损检查
            max_holding_days = self.risk_config.get('max_holding_days', 30)
            holding_days = (datetime.now().timestamp() - position.entry_time) / 86400
            
            if holding_days > max_holding_days:
                # 检查是否盈利
                if current_price <= position.entry_price:
                    logger.warning(f"触发时间止损: {position.symbol}, "
                                 f"持仓{holding_days:.1f}天未盈利")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"检查止损触发失败: {e}")
            return False
    
    def check_all_positions_stop_loss(
        self,
        positions: List[Position],
        current_prices: Dict[str, float]
    ) -> List[Position]:
        """
        检查所有持仓的止损条件
        
        Args:
            positions: 持仓列表
            current_prices: 当前价格字典 {symbol: price}
            
        Returns:
            需要平仓的持仓列表
        """
        positions_to_close = []
        
        for position in positions:
            try:
                symbol = position.symbol
                current_price = current_prices.get(symbol)
                
                if current_price is None:
                    logger.warning(f"无法获取{symbol}当前价格")
                    continue
                
                # 更新未实现盈亏
                position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
                position.unrealized_pnl_percent = (current_price - position.entry_price) / position.entry_price
                
                # 检查止损
                if self.check_stop_loss_trigger(position, current_price):
                    positions_to_close.append(position)
            except Exception as e:
                logger.error(f"检查持仓 {position.symbol} 止损失败: {e}")
                # 继续处理其他持仓
        
        if positions_to_close:
            logger.warning(f"发现{len(positions_to_close)}个持仓需要止损平仓")
        
        return positions_to_close
    
    def _get_today_trades_count(self) -> int:
        """获取今日交易次数"""
        try:
            # TODO: 从数据库查询今日交易记录
            # 暂时返回0
            return 0
        except Exception as e:
            logger.error(f"获取今日交易次数失败: {e}")
            return 0
    
    def get_risk_summary(self, account_balance: float, positions: List[Position]) -> Dict[str, Any]:
        """
        获取风险摘要
        
        Args:
            account_balance: 账户余额
            positions: 持仓列表
            
        Returns:
            风险摘要字典
        """
        try:
            total_position_value = sum(p.quantity * p.entry_price for p in positions)
            total_unrealized_pnl = sum(p.unrealized_pnl for p in positions)
            
            position_ratio = total_position_value / account_balance if account_balance > 0 else 0
            
            return {
                'account_balance': account_balance,
                'total_position_value': total_position_value,
                'total_unrealized_pnl': total_unrealized_pnl,
                'position_ratio': position_ratio,
                'position_count': len(positions),
                'risk_level': self._calculate_risk_level(position_ratio, total_unrealized_pnl, account_balance)
            }
        except Exception as e:
            logger.error(f"获取风险摘要失败: {e}")
            return {
                'account_balance': account_balance,
                'total_position_value': 0,
                'total_unrealized_pnl': 0,
                'position_ratio': 0,
                'position_count': 0,
                'risk_level': 'low'
            }
    
    def _calculate_risk_level(
        self,
        position_ratio: float,
        unrealized_pnl: float,
        account_balance: float
    ) -> str:
        """
        计算风险等级
        
        Returns:
            'low' | 'medium' | 'high'
        """
        try:
            pnl_ratio = unrealized_pnl / account_balance if account_balance > 0 else 0
            
            # 高风险条件
            if position_ratio > 0.7 or pnl_ratio < -0.05:
                return 'high'
            
            # 中等风险
            elif position_ratio > 0.5 or pnl_ratio < -0.02:
                return 'medium'
            
            # 低风险
            else:
                return 'low'
        except Exception as e:
            logger.error(f"计算风险等级失败: {e}")
            return 'low'


# 全局风控实例
risk_controller = RiskController()
