import uuid
from datetime import datetime
from typing import Dict, List

from sqlalchemy import delete, select
from sqlalchemy.exc import OperationalError

from app.db.session import TradingSessionLocal
from app.modules.monitoring.models import AlertNotificationRecord, AlertRuleRecord
from app.modules.monitoring.schemas import (
    AlertNotification,
    AlertRule,
    AlertSeverity,
    AlertType,
)

MAX_ALERTS = 100


class AlertManager:
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.alerts: List[AlertNotification] = []
        self.subscribers: List = []
        self._load()

    def _load(self) -> None:
        db = TradingSessionLocal()
        try:
            for record in db.execute(select(AlertRuleRecord)).scalars():
                self.rules[record.id] = self._to_rule(record)
            records = db.execute(
                select(AlertNotificationRecord).order_by(AlertNotificationRecord.timestamp.desc())
            ).scalars().all()
            self.alerts = [self._to_alert(r) for r in records]
        except OperationalError:
            self.rules = {}
            self.alerts = []
        finally:
            db.close()

    @staticmethod
    def _to_rule(record: AlertRuleRecord) -> AlertRule:
        return AlertRule(
            id=record.id,
            name=record.name,
            type=AlertType(record.type),
            market=record.market,
            symbol=record.symbol,
            threshold=record.threshold,
            severity=AlertSeverity(record.severity),
            enabled=record.enabled,
            created_at=record.created_at,
        )

    @staticmethod
    def _to_alert(record: AlertNotificationRecord) -> AlertNotification:
        return AlertNotification(
            id=record.id,
            rule_id=record.rule_id,
            type=AlertType(record.type),
            severity=AlertSeverity(record.severity),
            message=record.message,
            market=record.market,
            symbol=record.symbol,
            current_value=record.current_value,
            threshold=record.threshold,
            timestamp=record.timestamp,
            read=record.read,
        )

    def add_rule(self, rule: AlertRule) -> AlertRule:
        rule.id = str(uuid.uuid4())
        rule.created_at = datetime.now()
        db = TradingSessionLocal()
        try:
            db.add(AlertRuleRecord(
                id=rule.id,
                name=rule.name,
                type=rule.type.value,
                market=rule.market,
                symbol=rule.symbol,
                threshold=rule.threshold,
                severity=rule.severity.value,
                enabled=rule.enabled,
                created_at=rule.created_at,
            ))
            db.commit()
        finally:
            db.close()
        self.rules[rule.id] = rule
        return rule

    def remove_rule(self, rule_id: str) -> bool:
        if rule_id not in self.rules:
            return False
        db = TradingSessionLocal()
        try:
            db.execute(delete(AlertRuleRecord).where(AlertRuleRecord.id == rule_id))
            db.commit()
        finally:
            db.close()
        del self.rules[rule_id]
        return True

    def get_rules(self) -> List[AlertRule]:
        return list(self.rules.values())

    def get_rule(self, rule_id: str) -> AlertRule | None:
        return self.rules.get(rule_id)

    def toggle_rule(self, rule_id: str) -> bool:
        rule = self.rules.get(rule_id)
        if not rule:
            return False
        rule.enabled = not rule.enabled
        db = TradingSessionLocal()
        try:
            db.execute(
                AlertRuleRecord.__table__.update()
                .where(AlertRuleRecord.id == rule_id)
                .values(enabled=rule.enabled)
            )
            db.commit()
        finally:
            db.close()
        return True

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
        db = TradingSessionLocal()
        try:
            db.add(AlertNotificationRecord(
                id=alert.id,
                rule_id=alert.rule_id,
                type=alert.type.value,
                severity=alert.severity.value,
                message=alert.message,
                market=alert.market,
                symbol=alert.symbol,
                current_value=alert.current_value,
                threshold=alert.threshold,
                timestamp=alert.timestamp,
                read=alert.read,
            ))
            newest = db.execute(
                select(AlertNotificationRecord.id)
                .order_by(AlertNotificationRecord.timestamp.desc())
                .limit(MAX_ALERTS)
            ).scalars().all()
            keep_ids = set(newest)
            to_delete = db.execute(
                select(AlertNotificationRecord.id)
                .where(AlertNotificationRecord.id.not_in(keep_ids))
            ).scalars().all()
            for alert_id in to_delete:
                db.execute(delete(AlertNotificationRecord).where(AlertNotificationRecord.id == alert_id))
            db.commit()
        finally:
            db.close()

        self.alerts.insert(0, alert)
        if len(self.alerts) > MAX_ALERTS:
            self.alerts = self.alerts[:MAX_ALERTS]
        self.notify_subscribers(alert)
        return alert

    def get_alerts(self, limit: int = 20) -> List[AlertNotification]:
        return self.alerts[:limit]

    def mark_as_read(self, alert_id: str) -> bool:
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.read = True
                break
        else:
            return False
        db = TradingSessionLocal()
        try:
            db.execute(
                AlertNotificationRecord.__table__.update()
                .where(AlertNotificationRecord.id == alert_id)
                .values(read=True)
            )
            db.commit()
        finally:
            db.close()
        return True

    def mark_all_as_read(self) -> int:
        count = 0
        for alert in self.alerts:
            if not alert.read:
                alert.read = True
                count += 1
        db = TradingSessionLocal()
        try:
            db.execute(
                AlertNotificationRecord.__table__.update()
                .values(read=True)
            )
            db.commit()
        finally:
            db.close()
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