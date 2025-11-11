"""
通知告警模块
支持多种通知渠道（企业微信、钉钉、Telegram、邮件）
"""

import os
import requests
import smtplib
from typing import List, Dict, Any, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from loguru import logger

from config import get_config


class Notifier:
    """通知器类"""
    
    def __init__(self):
        """初始化通知器"""
        self.config = get_config()
        self.notification_config = self.config.get('notification', {})
        
        # 告警级别
        self.LEVEL_INFO = 'info'
        self.LEVEL_WARNING = 'warning'
        self.LEVEL_ERROR = 'error'
        self.LEVEL_CRITICAL = 'critical'
        
        logger.info("通知器初始化完成")
    
    def notify(
        self,
        title: str,
        message: str,
        level: str = 'info',
        channels: Optional[List[str]] = None
    ) -> bool:
        """
        发送通知
        
        Args:
            title: 标题
            message: 消息内容
            level: 告警级别 (info/warning/error/critical)
            channels: 通知渠道列表，None表示使用配置的默认渠道
        
        Returns:
            bool: 是否成功
        """
        try:
            # 如果未指定渠道，使用配置的默认渠道
            if channels is None:
                channels = self.notification_config.get('enabled_channels', [])
            
            # 根据级别过滤渠道（critical级别发送所有渠道）
            if level != self.LEVEL_CRITICAL:
                min_level = self.notification_config.get('min_level', 'warning')
                level_priority = {
                    'info': 0,
                    'warning': 1,
                    'error': 2,
                    'critical': 3
                }
                
                if level_priority.get(level, 0) < level_priority.get(min_level, 1):
                    logger.debug(f"通知级别 {level} 低于最小级别 {min_level}，跳过")
                    return False
            
            success_count = 0
            
            # 发送到各个渠道
            for channel in channels:
                try:
                    if channel == 'wechat':
                        if self._send_wechat(title, message, level):
                            success_count += 1
                    elif channel == 'dingtalk':
                        if self._send_dingtalk(title, message, level):
                            success_count += 1
                    elif channel == 'telegram':
                        if self._send_telegram(title, message, level):
                            success_count += 1
                    elif channel == 'email':
                        if self._send_email(title, message, level):
                            success_count += 1
                    else:
                        logger.warning(f"不支持的通知渠道: {channel}")
                        
                except Exception as e:
                    logger.error(f"发送{channel}通知失败: {e}")
            
            logger.info(f"通知已发送: {success_count}/{len(channels)} 个渠道成功")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
            return False
    
    def notify_stop_loss(self, symbol: str, entry_price: float, close_price: float, reason: str):
        """
        止损通知
        
        Args:
            symbol: 交易对
            entry_price: 入场价
            close_price: 平仓价
            reason: 止损原因
        """
        pnl_percent = (close_price / entry_price - 1) * 100
        
        title = f"⚠️ 止损触发: {symbol}"
        message = f"""
**止损触发通知**

交易对: {symbol}
入场价: ${entry_price:.2f}
平仓价: ${close_price:.2f}
盈亏: {pnl_percent:.2f}%
原因: {reason}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        self.notify(title, message, level=self.LEVEL_WARNING)
    
    def notify_order_executed(self, symbol: str, side: str, price: float, quantity: float):
        """
        订单执行通知
        
        Args:
            symbol: 交易对
            side: 方向
            price: 价格
            quantity: 数量
        """
        title = f"{'📈' if side == 'BUY' else '📉'} 订单执行: {symbol}"
        message = f"""
**订单执行通知**

交易对: {symbol}
方向: {side}
价格: ${price:.2f}
数量: {quantity}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        self.notify(title, message, level=self.LEVEL_INFO)
    
    def notify_system_error(self, error_type: str, error_message: str, stack_trace: str = None):
        """
        系统错误通知
        
        Args:
            error_type: 错误类型
            error_message: 错误信息
            stack_trace: 堆栈跟踪
        """
        title = f"🔴 系统错误: {error_type}"
        message = f"""
**系统错误通知**

错误类型: {error_type}
错误信息: {error_message}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        if stack_trace:
            message += f"\n堆栈跟踪:\n```\n{stack_trace[:500]}\n```"
        
        self.notify(title, message, level=self.LEVEL_CRITICAL)
    
    def notify_daily_summary(self, summary_data: Dict[str, Any]):
        """
        每日摘要通知
        
        Args:
            summary_data: 摘要数据
        """
        title = "📊 每日交易摘要"
        message = f"""
**每日交易摘要**

日期: {datetime.now().strftime('%Y-%m-%d')}

交易统计:
- 交易次数: {summary_data.get('trade_count', 0)}
- 成功率: {summary_data.get('success_rate', 0):.1f}%
- 今日盈亏: {summary_data.get('daily_pnl', 0):.2f} USDT

持仓情况:
- 当前持仓: {summary_data.get('position_count', 0)}
- 浮动盈亏: {summary_data.get('unrealized_pnl', 0):.2f} USDT

系统状态: 正常运行
"""
        
        self.notify(title, message, level=self.LEVEL_INFO, channels=['email'])
    
    # ==================== 各渠道实现方法 ====================
    
    def _send_wechat(self, title: str, message: str, level: str) -> bool:
        """
        发送企业微信机器人通知
        
        Args:
            title: 标题
            message: 消息
            level: 级别
        
        Returns:
            bool: 是否成功
        """
        try:
            webhook_url = os.getenv('WECHAT_WEBHOOK_URL')
            if not webhook_url:
                logger.warning("未配置企业微信Webhook URL")
                return False
            
            # 根据级别选择颜色
            color_map = {
                'info': 'info',
                'warning': 'warning',
                'error': 'warning',
                'critical': 'warning'
            }
            
            # 构建Markdown消息
            markdown_text = f"## {title}\n\n{message}"
            
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": markdown_text
                }
            }
            
            response = requests.post(webhook_url, json=data, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logger.debug("企业微信通知发送成功")
                    return True
                else:
                    logger.error(f"企业微信通知失败: {result.get('errmsg')}")
            
            return False
            
        except Exception as e:
            logger.error(f"发送企业微信通知失败: {e}")
            return False
    
    def _send_dingtalk(self, title: str, message: str, level: str) -> bool:
        """
        发送钉钉机器人通知
        
        Args:
            title: 标题
            message: 消息
            level: 级别
        
        Returns:
            bool: 是否成功
        """
        try:
            webhook_url = os.getenv('DINGTALK_WEBHOOK_URL')
            if not webhook_url:
                logger.warning("未配置钉钉Webhook URL")
                return False
            
            # 构建Markdown消息
            markdown_text = f"## {title}\n\n{message}"
            
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": markdown_text
                }
            }
            
            response = requests.post(webhook_url, json=data, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logger.debug("钉钉通知发送成功")
                    return True
                else:
                    logger.error(f"钉钉通知失败: {result.get('errmsg')}")
            
            return False
            
        except Exception as e:
            logger.error(f"发送钉钉通知失败: {e}")
            return False
    
    def _send_telegram(self, title: str, message: str, level: str) -> bool:
        """
        发送Telegram通知
        
        Args:
            title: 标题
            message: 消息
            level: 级别
        
        Returns:
            bool: 是否成功
        """
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            
            if not bot_token or not chat_id:
                logger.warning("未配置Telegram Bot Token或Chat ID")
                return False
            
            # 组合消息
            full_message = f"<b>{title}</b>\n\n{message}"
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": full_message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                logger.debug("Telegram通知发送成功")
                return True
            else:
                logger.error(f"Telegram通知失败: {response.text}")
            
            return False
            
        except Exception as e:
            logger.error(f"发送Telegram通知失败: {e}")
            return False
    
    def _send_email(self, title: str, message: str, level: str) -> bool:
        """
        发送邮件通知
        
        Args:
            title: 标题
            message: 消息
            level: 级别
        
        Returns:
            bool: 是否成功
        """
        try:
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            smtp_user = os.getenv('SMTP_USER')
            smtp_password = os.getenv('SMTP_PASSWORD')
            email_to = os.getenv('EMAIL_TO')
            
            if not all([smtp_server, smtp_user, smtp_password, email_to]):
                logger.warning("未配置完整的邮件参数")
                return False
            
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = email_to
            msg['Subject'] = f"[QuantAITrade] {title}"
            
            # 邮件正文（HTML格式）
            html_message = f"""
            <html>
                <body>
                    <h2>{title}</h2>
                    <pre>{message}</pre>
                    <hr>
                    <p style="color: gray; font-size: 0.9em;">
                        此邮件由QuantAITrade系统自动发送<br>
                        发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(html_message, 'html'))
            
            # 发送邮件
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            
            logger.debug("邮件通知发送成功")
            return True
            
        except Exception as e:
            logger.error(f"发送邮件通知失败: {e}")
            return False


# 全局实例
notifier = Notifier()
