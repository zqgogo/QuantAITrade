import uuid
from datetime import datetime
from typing import Dict, List

from app.modules.monitoring.schemas import (
    AlertNotification,
    AlertRule,
    AlertSeverity,
    AlertType,
)


class AlertManager:
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: List[AlertNotification] = []
        self.subscribers: List = []
    
    def add_rule(self, rule: AlertRule) -> AlertRule:
        rule.id = str(uuid.uuid4())
        rule.created_at = datetime.now()
        self.rules[rule.id] = rule
        return rule
    
    def remove_rule(self, rule_id: str) -> bool:
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False
    
    def get_rules(self) -> List[AlertRule]:
        return list(self.rules.values())
    
    def get_rule(self, rule_id: str) -> AlertRule | None:
        return self.rules.get(rule_id)
    
    def toggle_rule(self, rule_id: str) -> bool:
        rule = self.rules.get(rule_id)
        if rule:
            rule.enabled = not rule.enabled
            return True
        return False
    
    def trigger_alert(
        self,
        rule_id: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
        market: str,
        symbol: str,
        current_value: float,
        threshold: float,
    ) -> AlertNotification:
        alert = AlertNotification(
            id=str(uuid.uuid4()),
            rule_id=rule_id,
            type=alert_type,
            severity=severity,
            message=message,
            market=market,
            symbol=symbol,
            current_value=current_value,
            threshold=threshold,
            timestamp=datetime.now(),
            read=False,
        )
        self.alerts.insert(0, alert)
        if len(self.alerts) > 100:
            self.alerts = self.alerts[:100]
        self.notify_subscribers(alert)
        return alert
    
    def get_alerts(self, limit: int = 20) -> List[AlertNotification]:
        return self.alerts[:limit]
    
    def mark_as_read(self, alert_id: str) -> bool:
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.read = True
                return True
        return False
    
    def mark_all_as_read(self) -> int:
        count = 0
        for alert in self.alerts:
            if not alert.read:
                alert.read = True
                count += 1
        return count
    
    def subscribe(self, callback):
        self.subscribers.append(callback)
    
    def unsubscribe(self, callback):
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def notify_subscribers(self, alert: AlertNotification):
        for callback in self.subscribers:
            try:
                callback(alert)
            except Exception:
                pass


alert_manager = AlertManager()
