"""
交易所连接器
封装 Binance API 交易接口，提供统一的交易操作接口
"""

import os
import time
from typing import Optional, List, Dict, Any
from loguru import logger
import ccxt
from datetime import datetime

from data.models import Order, OrderSide, OrderType, OrderStatus
from config import get_config


class ExchangeConnector:
    """交易所连接器类"""
    
    def __init__(self):
        """初始化交易所连接"""
        self.config = get_config()
        self.exchange: Optional[ccxt.binance] = None
        self.connected = False
        
        # 从配置读取参数
        exchange_config = self.config.get('exchange', {})
        self.use_testnet = exchange_config.get('use_testnet', True)
        self.api_timeout = exchange_config.get('api_timeout', 30) * 1000  # 转换为毫秒
        self.max_retries = exchange_config.get('max_retries', 3)
        self.retry_delay = exchange_config.get('retry_delay', 2)
        
        # API密钥从环境变量读取
        self.api_key = os.getenv('BINANCE_API_KEY', '')
        self.api_secret = os.getenv('BINANCE_API_SECRET', '')
        
        logger.info(f"交易所连接器初始化 - 测试网模式: {self.use_testnet}")
    
    def connect(self) -> bool:
        """
        建立与交易所的连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            # 初始化 ccxt binance
            self.exchange = ccxt.binance({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'timeout': self.api_timeout,
                'enableRateLimit': True,  # 启用限流保护
            })
            
            # 设置测试网
            if self.use_testnet:
                self.exchange.set_sandbox_mode(True)
                logger.info("已启用 Binance 测试网模式")
            
            # 验证连接
            if self.api_key and self.api_secret:
                try:
                    balance = self.exchange.fetch_balance()
                    logger.success(f"交易所连接成功 - 账户类型: {'测试网' if self.use_testnet else '实盘'}")
                    self.connected = True
                    return True
                except Exception as e:
                    logger.error(f"API 密钥验证失败: {e}")
                    # 在测试模式下仍然认为连接成功
                    if self.use_testnet:
                        logger.info("测试模式下忽略API密钥验证失败")
                        self.connected = True
                        return True
                    self.connected = False
                    return False
            else:
                logger.warning("未配置 API 密钥，仅支持查询功能")
                self.connected = True
                return True
                
        except ccxt.AuthenticationError as e:
            logger.error(f"API 密钥验证失败: {e}")
            # 在测试模式下仍然认为连接成功
            if self.use_testnet:
                logger.info("测试模式下忽略API密钥验证失败")
                self.connected = True
                return True
            self.connected = False
            return False
        except ccxt.NetworkError as e:
            logger.error(f"网络连接失败: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"交易所连接失败: {e}")
            # 在测试模式下仍然认为连接成功
            if self.use_testnet:
                logger.info("测试模式下忽略连接失败")
                self.connected = True
                return True
            self.connected = False
            return False
    
    def get_account_balance(self) -> Dict[str, Any]:
        """
        获取账户余额信息
        
        Returns:
            dict: 余额信息，格式 {'USDT': {'free': 100.0, 'used': 0.0, 'total': 100.0}}
        """
        if not self.connected:
            logger.error("交易所未连接")
            # 在测试模式下返回模拟余额
            if self.use_testnet:
                return {'USDT': {'free': 10000.0, 'used': 0.0, 'total': 10000.0}}
            return {}
        
        try:
            balance = self.exchange.fetch_balance()
            # 过滤出非零余额
            result = {}
            for currency, info in balance['total'].items():
                if info > 0:
                    result[currency] = {
                        'free': balance['free'].get(currency, 0),
                        'used': balance['used'].get(currency, 0),
                        'total': info
                    }
            
            logger.debug(f"获取账户余额成功: {list(result.keys())}")
            return result
            
        except Exception as e:
            logger.error(f"获取账户余额失败: {e}")
            # 在测试模式下返回模拟余额
            if self.use_testnet:
                return {'USDT': {'free': 10000.0, 'used': 0.0, 'total': 10000.0}}
            return {}
    
    def place_market_order(self, symbol: str, side: OrderSide, quantity: float) -> Optional[Order]:
        """
        下市价单
        
        Args:
            symbol: 交易对，如 'BTCUSDT'
            side: 订单方向 (BUY/SELL)
            quantity: 订单数量
            
        Returns:
            Order: 订单对象，失败返回 None
        """
        if not self.connected:
            logger.error("交易所未连接，无法下单")
            return None
        
        if not self.api_key or not self.api_secret:
            logger.error("未配置 API 密钥，无法下单")
            return None
        
        try:
            # 调用 ccxt 下单
            side_str = 'buy' if side == OrderSide.BUY else 'sell'
            
            logger.info(f"准备下市价单: {symbol} {side_str.upper()} {quantity}")
            
            # 重试机制
            for attempt in range(self.max_retries):
                try:
                    result = self.exchange.create_market_order(
                        symbol=symbol,
                        side=side_str,
                        amount=quantity
                    )
                    
                    # 构建 Order 对象
                    order = Order(
                        symbol=symbol,
                        side=side,
                        order_type=OrderType.MARKET,
                        quantity=quantity,
                        price=result.get('average') or result.get('price'),
                        order_id=str(result['id']),
                        client_order_id=result.get('clientOrderId'),
                        executed_qty=result.get('filled', 0),
                        status=self._parse_order_status(result['status']),
                        created_time=int(result.get('timestamp', time.time() * 1000) / 1000),
                        updated_time=int(time.time())
                    )
                    
                    logger.success(f"市价单提交成功: {order.order_id} - {symbol} {side_str.upper()} {quantity}")
                    return order
                    
                except ccxt.NetworkError as e:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"网络错误，{self.retry_delay}秒后重试 ({attempt+1}/{self.max_retries}): {e}")
                        time.sleep(self.retry_delay)
                    else:
                        raise
                except ccxt.ExchangeError as e:
                    logger.error(f"交易所拒绝订单: {e}")
                    raise
                    
        except ccxt.InsufficientFunds as e:
            logger.error(f"余额不足: {e}")
            return None
        except ccxt.InvalidOrder as e:
            logger.error(f"无效订单: {e}")
            return None
        except Exception as e:
            logger.error(f"下市价单失败: {e}")
            return None
    
    def place_limit_order(self, symbol: str, side: OrderSide, price: float, quantity: float) -> Optional[Order]:
        """
        下限价单
        
        Args:
            symbol: 交易对
            side: 订单方向
            price: 限价
            quantity: 数量
            
        Returns:
            Order: 订单对象，失败返回 None
        """
        if not self.connected:
            logger.error("交易所未连接，无法下单")
            return None
        
        if not self.api_key or not self.api_secret:
            logger.error("未配置 API 密钥，无法下单")
            return None
        
        try:
            side_str = 'buy' if side == OrderSide.BUY else 'sell'
            
            logger.info(f"准备下限价单: {symbol} {side_str.upper()} {quantity} @ {price}")
            
            # 重试机制
            for attempt in range(self.max_retries):
                try:
                    result = self.exchange.create_limit_order(
                        symbol=symbol,
                        side=side_str,
                        amount=quantity,
                        price=price
                    )
                    
                    order = Order(
                        symbol=symbol,
                        side=side,
                        order_type=OrderType.LIMIT,
                        quantity=quantity,
                        price=price,
                        order_id=str(result['id']),
                        client_order_id=result.get('clientOrderId'),
                        executed_qty=result.get('filled', 0),
                        status=self._parse_order_status(result['status']),
                        created_time=int(result.get('timestamp', time.time() * 1000) / 1000),
                        updated_time=int(time.time())
                    )
                    
                    logger.success(f"限价单提交成功: {order.order_id}")
                    return order
                    
                except ccxt.NetworkError as e:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"网络错误，{self.retry_delay}秒后重试 ({attempt+1}/{self.max_retries})")
                        time.sleep(self.retry_delay)
                    else:
                        raise
                except ccxt.ExchangeError as e:
                    logger.error(f"交易所拒绝订单: {e}")
                    raise
                        
        except Exception as e:
            logger.error(f"下限价单失败: {e}")
            return None
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """
        撤销订单
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            bool: 是否成功
        """
        if not self.connected:
            logger.error("交易所未连接")
            return False
        
        try:
            self.exchange.cancel_order(order_id, symbol)
            logger.info(f"订单撤销成功: {order_id}")
            return True
        except Exception as e:
            logger.error(f"订单撤销失败: {e}")
            return False
    
    def get_order_status(self, symbol: str, order_id: str) -> Optional[OrderStatus]:
        """
        查询订单状态
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            OrderStatus: 订单状态
        """
        if not self.connected:
            logger.error("交易所未连接")
            return None
        
        try:
            order = self.exchange.fetch_order(order_id, symbol)
            status = self._parse_order_status(order['status'])
            logger.debug(f"订单状态查询: {order_id} - {status.value}")
            return status
        except Exception as e:
            logger.error(f"查询订单状态失败: {e}")
            return None
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """
        获取未成交订单
        
        Args:
            symbol: 交易对，None 表示所有交易对
            
        Returns:
            List[Order]: 订单列表
        """
        if not self.connected:
            logger.error("交易所未连接")
            return []
        
        try:
            orders = self.exchange.fetch_open_orders(symbol)
            result = []
            
            for order_data in orders:
                order = Order(
                    symbol=order_data['symbol'],
                    side=OrderSide.BUY if order_data['side'] == 'buy' else OrderSide.SELL,
                    order_type=OrderType.MARKET if order_data['type'] == 'market' else OrderType.LIMIT,
                    quantity=order_data['amount'],
                    price=order_data.get('price'),
                    order_id=str(order_data['id']),
                    client_order_id=order_data.get('clientOrderId'),
                    executed_qty=order_data.get('filled', 0),
                    status=self._parse_order_status(order_data['status']),
                    created_time=int(order_data.get('timestamp', time.time() * 1000) / 1000),
                    updated_time=int(time.time())
                )
                result.append(order)
            
            logger.debug(f"查询到 {len(result)} 个未成交订单")
            return result
            
        except Exception as e:
            logger.error(f"查询未成交订单失败: {e}")
            return []
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        获取当前市场价格
        
        Args:
            symbol: 交易对
            
        Returns:
            float: 当前价格
        """
        if not self.connected:
            logger.error("交易所未连接")
            return None
        
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            price = ticker['last']
            logger.debug(f"{symbol} 当前价格: {price}")
            return price
        except Exception as e:
            logger.error(f"获取价格失败: {e}")
            return None
    
    def _parse_order_status(self, status_str: str) -> OrderStatus:
        """
        解析订单状态字符串
        
        Args:
            status_str: ccxt 返回的状态字符串
            
        Returns:
            OrderStatus: 订单状态枚举
        """
        status_map = {
            'open': OrderStatus.NEW,
            'closed': OrderStatus.FILLED,
            'canceled': OrderStatus.CANCELED,
            'cancelled': OrderStatus.CANCELED,
            'rejected': OrderStatus.REJECTED,
            'expired': OrderStatus.EXPIRED,
        }
        return status_map.get(status_str.lower(), OrderStatus.NEW)
    
    def close(self):
        """关闭连接"""
        if self.exchange:
            try:
                self.exchange.close()
                logger.info("交易所连接已关闭")
            except Exception as e:
                logger.error(f"关闭连接失败: {e}")
        self.connected = False


# 全局实例
exchange_connector = ExchangeConnector()
