import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.monitoring.alert_manager import AlertManager, alert_manager
from app.modules.monitoring.schemas import AlertSeverity, AlertType

HEADERS = {"X-API-Key": "dev-secret-key"}


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


def _create_price_rule(client: TestClient) -> str:
    resp = client.post(
        "/api/v1/monitoring/alerts/price",
        json={
            "name": "BTC price alert",
            "market": "crypto",
            "symbol": "BTCUSDT",
            "type": "price_below",
            "threshold": 50000,
            "severity": "critical",
        },
        headers=HEADERS,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def test_create_price_alert_rule(client: TestClient) -> None:
    rule_id = _create_price_rule(client)
    assert rule_id

    resp = client.get("/api/v1/monitoring/alerts/rules", headers=HEADERS)
    assert resp.status_code == 200
    rules = resp.json()["rules"]
    assert any(r["id"] == rule_id for r in rules)


def test_toggle_and_delete_rule(client: TestClient) -> None:
    rule_id = _create_price_rule(client)

    resp = client.patch(f"/api/v1/monitoring/alerts/rules/{rule_id}/toggle", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    resp = client.delete(f"/api/v1/monitoring/alerts/rules/{rule_id}", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    resp = client.get("/api/v1/monitoring/alerts/rules", headers=HEADERS)
    assert all(r["id"] != rule_id for r in resp.json()["rules"])


def test_rule_and_alert_persist_to_db(client: TestClient) -> None:
    rule_id = _create_price_rule(client)

    alert = alert_manager.trigger_alert(
        rule_id=rule_id,
        alert_type=AlertType.PRICE_BELOW,
        severity=AlertSeverity.CRITICAL,
        message="BTC below 50000",
        market="crypto",
        symbol="BTCUSDT",
        current_value=48000,
        threshold=50000,
    )

    resp = client.get(
        "/api/v1/monitoring/alerts/notifications",
        params={"limit": 20},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    alerts = resp.json()["alerts"]
    assert any(a["id"] == alert.id for a in alerts)

    reloaded = AlertManager()
    assert reloaded.get_rule(rule_id) is not None
    assert any(a.id == alert.id for a in reloaded.alerts)


def test_mark_alert_read(client: TestClient) -> None:
    rule_id = _create_price_rule(client)
    alert = alert_manager.trigger_alert(
        rule_id=rule_id,
        alert_type=AlertType.PRICE_ABOVE,
        severity=AlertSeverity.WARNING,
        message="BTC above 60000",
        market="crypto",
        symbol="BTCUSDT",
        current_value=61000,
        threshold=60000,
    )

    resp = client.patch(f"/api/v1/monitoring/alerts/notifications/{alert.id}/read", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    resp = client.get(
        "/api/v1/monitoring/alerts/notifications",
        params={"limit": 20},
        headers=HEADERS,
    )
    assert any(a["id"] == alert.id and a["read"] is True for a in resp.json()["alerts"])