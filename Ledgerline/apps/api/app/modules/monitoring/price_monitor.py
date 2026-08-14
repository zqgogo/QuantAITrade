import asyncio
from datetime import datetime
from typing import Dict

from app.modules.market.repository import OhlcvRepository
from app.modules.monitoring.alert_manager import alert_manager
from app.modules.monitoring.schemas import (
    AlertType,
    PriceUpdate,
)


class PriceMonitor:
    def __init__(self):
        self.ohlcv_repository = OhlcvRepository()
        self.last_prices: Dict[str, float] = {}
        self.last_update: Dict[str, datetime] = {}
        self.monitor_tasks = {}
        self.subscribers: list = []
    
    async def get_current_price(self, market: str, symbol: str) -> float | None:
        for interval in ["1m", "5m", "15m", "1h", "4h", "1d"]:
            bars = self.ohlcv_repository.get_ohlcv(market, symbol, interval, limit=1)
            if bars:
                return float(bars[-1].close)
        return None
    
    async def check_price_alerts(self, market: str, symbol: str):
        price = await self.get_current_price(market, symbol)
        if price is None:
            return
        
        key = f"{market}:{symbol}"
        last_price = self.last_prices.get(key, price)
        self.last_prices[key] = price
        self.last_update[key] = datetime.now()
        
        price_update = PriceUpdate(
            market=market,
            symbol=symbol,
            price=price,
            timestamp=datetime.now(),
            change_24h=None,
        )
        self.notify_price_update(price_update)
        
        for rule_id, rule in alert_manager.rules.items():
            if not rule.enabled:
                continue
            if rule.market != market or rule.symbol != symbol:
                continue
            
            if rule.type == AlertType.PRICE_ABOVE and price >= rule.threshold:
                alert_manager.trigger_alert(
                    rule_id=rule_id,
                    alert_type=AlertType.PRICE_ABOVE,
                    severity=rule.severity,
                    message=f"Price {symbol} above threshold: ${price:.2f} >= ${rule.threshold:.2f}",
                    market=market,
                    symbol=symbol,
                    current_value=price,
                    threshold=rule.threshold,
                )
            
            elif rule.type == AlertType.PRICE_BELOW and price <= rule.threshold:
                alert_manager.trigger_alert(
                    rule_id=rule_id,
                    alert_type=AlertType.PRICE_BELOW,
                    severity=rule.severity,
                    message=f"Price {symbol} below threshold: ${price:.2f} <= ${rule.threshold:.2f}",
                    market=market,
                    symbol=symbol,
                    current_value=price,
                    threshold=rule.threshold,
                )
            
            elif rule.type == AlertType.PRICE_CHANGE and last_price > 0:
                change_pct = abs((price - last_price) / last_price * 100)
                if change_pct >= rule.threshold:
                    direction = "up" if price > last_price else "down"
                    alert_manager.trigger_alert(
                        rule_id=rule_id,
                        alert_type=AlertType.PRICE_CHANGE,
                        severity=rule.severity,
                        message=f"Price {symbol} changed {direction} by {change_pct:.2f}%: ${last_price:.2f} -> ${price:.2f}",
                        market=market,
                        symbol=symbol,
                        current_value=change_pct,
                        threshold=rule.threshold,
                    )
    
    async def start_monitor(self, market: str, symbol: str, interval: int = 5):
        key = f"{market}:{symbol}"
        if key in self.monitor_tasks:
            return
        
        async def monitor_loop():
            while True:
                await self.check_price_alerts(market, symbol)
                await asyncio.sleep(interval)
        
        task = asyncio.create_task(monitor_loop())
        self.monitor_tasks[key] = task
    
    async def stop_monitor(self, market: str, symbol: str):
        key = f"{market}:{symbol}"
        task = self.monitor_tasks.get(key)
        if task:
            task.cancel()
            del self.monitor_tasks[key]
    
    def get_monitored_symbols(self) -> list[str]:
        return list(self.monitor_tasks.keys())
    
    def subscribe(self, callback):
        self.subscribers.append(callback)
    
    def unsubscribe(self, callback):
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def notify_price_update(self, update: PriceUpdate):
        for callback in self.subscribers:
            try:
                callback(update)
            except Exception:
                pass


price_monitor = PriceMonitor()
