"""
MA交叉策略
基于短期和长期移动平均线交叉的交易策略
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from loguru import logger

from src.strategy.base_strategy import BaseStrategy
from data.models import Signal, SignalType


class MACrossStrategy(BaseStrategy):
    """
    MA交叉策略实现
    """
    
    def __init__(self, params: dict = None):
        """
        初始化MA交叉策略
        
        Args:
            params: 策略参数
                - short_window: 短期均线周期（默认5）
                - long_window: 长期均线周期（默认20）
                - min_cross_distance: 最小交叉距离，过滤假信号（默认0.001）
        """
        default_params = {
            'short_window': 5,
            'long_window': 20,
            'min_cross_distance': 0.001
        }
        
        if params:
            default_params.update(params)
        
        super().__init__('MA_Cross', default_params)
    
    def get_min_periods(self) -> int:
        """需要至少long_window条数据"""
        return self.params['long_window'] + 5
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算均线指标
        
        Args:
            df: K线数据
            
        Returns:
            添加了MA指标的DataFrame
        """
        try:
            short_window = self.params['short_window']
            long_window = self.params['long_window']
            
            # 确保数据足够
            if len(df) < long_window:
                logger.warning(f"数据不足，需要至少 {long_window} 条")
                return df
            
            # 计算短期和长期均线
            df['ma_short'] = df['close'].rolling(window=short_window).mean()
            df['ma_long'] = df['close'].rolling(window=long_window).mean()
            
            # 计算均线差值（用于判断交叉）
            df['ma_diff'] = df['ma_short'] - df['ma_long']
            
            return df
        except Exception as e:
            logger.error(f"计算均线指标失败: {e}")
            return df
    
    def generate_signal(self, df: pd.DataFrame) -> Optional[Signal]:
        """
        生成交易信号
        
        Args:
            df: 包含均线指标的DataFrame
            
        Returns:
            Signal对象或None
        """
        try:
            if len(df) < 2:
                return None
            
            # 获取最近两个数据点
            current = df.iloc[-1]
            previous = df.iloc[-2]
            
            # 检查数据有效性
            if pd.isna(current['ma_short']) or pd.isna(current['ma_long']):
                return None
            
            current_diff = current['ma_diff']
            previous_diff = previous['ma_diff']
            min_distance = self.params['min_cross_distance']
            
            signal_type = None
            reason = ""
            
            # 金叉：短期均线上穿长期均线
            if previous_diff < 0 and current_diff > 0:
                # 检查交叉强度（过滤假信号）
                if abs(current_diff / current['close']) > min_distance:
                    signal_type = SignalType.BUY
                    reason = f"金叉: MA{self.params['short_window']} 上穿 MA{self.params['long_window']}"
                    logger.info(f"{reason}, 当前价格: {current['close']:.2f}")
            
            # 死叉：短期均线下穿长期均线
            elif previous_diff > 0 and current_diff < 0:
                # 检查交叉强度
                if abs(current_diff / current['close']) > min_distance:
                    signal_type = SignalType.SELL
                    reason = f"死叉: MA{self.params['short_window']} 下穿 MA{self.params['long_window']}"
                    logger.info(f"{reason}, 当前价格: {current['close']:.2f}")
            
            # 生成信号对象
            if signal_type:
                # 计算信号置信度（基于均线距离）
                ma_distance = abs(current_diff / current['close'])
                confidence = min(ma_distance / (min_distance * 10), 1.0)  # 归一化到0-1
                
                # 确保symbol字段存在
                symbol = current.get('symbol', 'UNKNOWN')
                if symbol == 'UNKNOWN' and hasattr(self, '_current_symbol'):
                    symbol = self._current_symbol
                
                signal = Signal(
                    strategy_name=self.name,
                    symbol=symbol,
                    signal_type=signal_type,
                    price=float(current['close']),
                    confidence=confidence,
                    reason=reason,
                    parameters={
                        'ma_short': float(current['ma_short']),
                        'ma_long': float(current['ma_long']),
                        'ma_diff': float(current_diff)
                    }
                )
                
                return signal
            
            return None
        except Exception as e:
            logger.error(f"生成交易信号失败: {e}")
            return None
    
    def validate_parameters(self, params: dict) -> bool:
        """
        验证参数有效性
        
        Args:
            params: 待验证的参数
            
        Returns:
            是否有效
        """
        # 检查必需参数
        if 'short_window' in params:
            if not isinstance(params['short_window'], int) or params['short_window'] < 2:
                logger.error("short_window 必须是大于1的整数")
                return False
        
        if 'long_window' in params:
            if not isinstance(params['long_window'], int) or params['long_window'] < 5:
                logger.error("long_window 必须是大于4的整数")
                return False
        
        # 短期均线必须小于长期均线
        short = params.get('short_window', self.params['short_window'])
        long = params.get('long_window', self.params['long_window'])
        
        if short >= long:
            logger.error(f"short_window ({short}) 必须小于 long_window ({long})")
            return False
        
        return True
