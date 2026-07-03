"""
策略基类
定义所有策略的统一接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import pandas as pd
from loguru import logger

from data.models import Signal, SignalType, StopLossType


class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, name: str, params: Dict[str, Any]):
        """
        初始化策略
        
        Args:
            name: 策略名称
            params: 策略参数
        """
        self.name = name
        self.params = params
        self.enabled = True
        logger.info(f"初始化策略: {name}, 参数: {params}")
    
    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标
        
        Args:
            df: K线数据DataFrame，包含 open, high, low, close, volume
            
        Returns:
            添加了指标列的DataFrame
        """
        pass
    
    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> Optional[Signal]:
        """
        生成交易信号
        
        Args:
            df: 包含指标的DataFrame
            
        Returns:
            Signal对象或None
        """
        pass
    
    def on_data(self, df: pd.DataFrame) -> Optional[Signal]:
        """
        接收K线数据并生成信号（主入口）
        
        Args:
            df: K线数据DataFrame
            
        Returns:
            Signal对象或None
        """
        if not self.enabled:
            logger.debug(f"策略 {self.name} 已禁用")
            return None
        
        if df is None or len(df) < self.get_min_periods():
            logger.warning(f"策略 {self.name} 数据不足，需要至少 {self.get_min_periods()} 条")
            return None
        
        try:
            # 确保必要的列存在
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_columns):
                logger.warning(f"策略 {self.name} 数据缺少必要列")
                return None
            
            # 确保数据不为空
            if df.empty:
                logger.warning(f"策略 {self.name} 数据为空")
                return None
            
            # 计算指标
            df_with_indicators = self.calculate_indicators(df.copy())
            
            # 生成信号
            signal = self.generate_signal(df_with_indicators)
            
            if signal:
                logger.info(f"策略 {self.name} 生成信号: {signal.signal_type.value} @ {signal.price}")
            
            return signal
            
        except Exception as e:
            logger.error(f"策略 {self.name} 生成信号失败: {e}")
            return None
    
    def get_min_periods(self) -> int:
        """
        获取策略所需的最小数据周期数
        
        Returns:
            最小周期数
        """
        return 50  # 默认50条
    
    def get_parameters(self) -> Dict[str, Any]:
        """获取当前策略参数"""
        return self.params.copy()
    
    def update_parameters(self, new_params: Dict[str, Any]) -> bool:
        """
        更新策略参数
        
        Args:
            new_params: 新参数字典
            
        Returns:
            是否更新成功
        """
        try:
            # 验证参数
            if not self.validate_parameters(new_params):
                logger.error(f"策略 {self.name} 参数验证失败: {new_params}")
                return False
            
            self.params.update(new_params)
            logger.info(f"策略 {self.name} 参数已更新: {new_params}")
            return True
            
        except Exception as e:
            logger.error(f"更新参数失败: {e}")
            return False
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """
        验证参数有效性
        
        Args:
            params: 待验证的参数
            
        Returns:
            是否有效
        """
        # 子类可以覆盖此方法实现自定义验证
        return True
    
    def calculate_stop_loss_price(
        self,
        entry_price: float,
        stop_loss_config: Dict[str, Any],
        df: pd.DataFrame
    ) -> tuple[float, StopLossType]:
        """
        计算止损价格
        
        Args:
            entry_price: 入场价格
            stop_loss_config: 止损配置
            df: K线数据
            
        Returns:
            (止损价格, 止损类型)
        """
        stop_type = stop_loss_config.get('type', 'fixed_percent')
        
        if stop_type == 'fixed_percent':
            # 固定百分比止损
            percent = stop_loss_config.get('stop_loss_percent', 0.03)
            stop_price = entry_price * (1 - percent)
            return stop_price, StopLossType.FIXED_PERCENT
            
        elif stop_type == 'key_level':
            # 关键点位止损
            lookback = stop_loss_config.get('support_lookback_days', 20)
            support_price = self._find_support_level(df, lookback)
            stop_price = support_price * 0.99  # 支撑位下方1%
            return stop_price, StopLossType.KEY_LEVEL
            
        elif stop_type == 'atr_based':
            # ATR动态止损
            multiplier = stop_loss_config.get('atr_multiplier', 2.0)
            atr = self._calculate_atr(df)
            stop_price = entry_price - (atr * multiplier)
            return stop_price, StopLossType.ATR_BASED
            
        else:
            # 默认使用3%固定止损
            stop_price = entry_price * 0.97
            return stop_price, StopLossType.FIXED_PERCENT
    
    def _find_support_level(self, df: pd.DataFrame, lookback: int) -> float:
        """
        寻找支撑位
        
        Args:
            df: K线数据
            lookback: 回看周期
            
        Returns:
            支撑位价格
        """
        if len(df) < lookback:
            lookback = len(df)
        
        recent_lows = df['low'].tail(lookback)
        support = recent_lows.min()
        
        return support
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        计算ATR（平均真实波动幅度）
        
        Args:
            df: K线数据
            period: 计算周期
            
        Returns:
            ATR值
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        # True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr.iloc[-1] if not atr.empty else 0.0
    
    def enable(self):
        """启用策略"""
        self.enabled = True
        logger.info(f"策略 {self.name} 已启用")
    
    def disable(self):
        """禁用策略"""
        self.enabled = False
        logger.info(f"策略 {self.name} 已禁用")
    
    def __str__(self) -> str:
        """字符串表示"""
        status = "启用" if self.enabled else "禁用"
        return f"<Strategy: {self.name} ({status})>"
    
    def __repr__(self) -> str:
        """详细表示"""
        return f"<Strategy: {self.name}, params={self.params}, enabled={self.enabled}>"
