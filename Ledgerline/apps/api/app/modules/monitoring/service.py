from typing import List

from app.modules.monitoring.alert_manager import alert_manager
from app.modules.monitoring.price_monitor import price_monitor
from app.modules.monitoring.schemas import (
    AlertRule,
    AlertRuleListResponse,
    AlertListResponse,
    PriceAlertRequest,
    PriceUpdate,
    SignalAlertRequest,
)


class MonitoringService:
    def create_price_alert(self, request: PriceAlertRequest) -> AlertRule:
        rule = AlertRule(
            name=request.name,
            type=request.type,
            market=request.market,
            symbol=request.symbol,
            threshold=request.threshold,
            severity=request.severity,
            enabled=True,
        )
        return alert_manager.add_rule(rule)
    
    def create_signal_alert(self, request: SignalAlertRequest) -> AlertRule:
        rule = AlertRule(
            name=f"Signal Alert - {request.strategy_name}",
            type="signal_alert",
            market=request.market,
            symbol=request.symbol,
            threshold=0,
            severity="warning",
            enabled=True,
        )
        return alert_manager.add_rule(rule)
    
    def get_all_rules(self) -> AlertRuleListResponse:
        return AlertRuleListResponse(rules=alert_manager.get_rules())
    
    def get_rule(self, rule_id: str) -> AlertRule | None:
        return alert_manager.get_rule(rule_id)
    
    def delete_rule(self, rule_id: str) -> bool:
        return alert_manager.remove_rule(rule_id)
    
    def toggle_rule(self, rule_id: str) -> bool:
        return alert_manager.toggle_rule(rule_id)
    
    def get_alerts(self, limit: int = 20) -> AlertListResponse:
        return AlertListResponse(alerts=alert_manager.get_alerts(limit))
    
    def mark_alert_read(self, alert_id: str) -> bool:
        return alert_manager.mark_as_read(alert_id)
    
    def mark_all_alerts_read(self) -> int:
        return alert_manager.mark_all_as_read()
    
    async def start_price_monitor(self, market: str, symbol: str, interval: int = 5):
        await price_monitor.start_monitor(market, symbol, interval)
    
    async def stop_price_monitor(self, market: str, symbol: str):
        await price_monitor.stop_monitor(market, symbol)
    
    def get_monitored_symbols(self) -> List[str]:
        return price_monitor.get_monitored_symbols()
    
    async def get_current_price(self, market: str, symbol: str) -> PriceUpdate | None:
        from datetime import datetime
        price = await price_monitor.get_current_price(market, symbol)
        if price is None:
            return None
        timestamp = price_monitor.last_update.get(f"{market}:{symbol}") or datetime.now()
        return PriceUpdate(
            market=market,
            symbol=symbol,
            price=price,
            timestamp=timestamp,
        )


monitoring_service = MonitoringService()
