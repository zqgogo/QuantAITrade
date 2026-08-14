import json

import pytest
from fastapi.testclient import TestClient

from app.main import app

HEADERS = {"X-API-Key": "dev-secret-key"}


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


def _seed_portfolio(client: TestClient) -> int:
    resp = client.post("/api/v1/trading/workspaces", json={"name": "ws"}, headers=HEADERS)
    assert resp.status_code == 200
    resp = client.post(
        "/api/v1/trading/portfolios",
        json={"workspace_id": resp.json()["id"], "name": "pf"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    return resp.json()["id"]


def _record(client: TestClient, portfolio_id: int, **kwargs) -> dict:
    payload = {
        "portfolio_id": portfolio_id,
        "market": "crypto",
        "symbol": "BTCUSDT",
        "side": "buy",
        **kwargs,
    }
    resp = client.post("/api/v1/trading/transactions", json=payload, headers=HEADERS)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _summary(client: TestClient, portfolio_id: int, current_price: float) -> dict:
    resp = client.get(
        f"/api/v1/trading/portfolios/{portfolio_id}/summary",
        params={"current_prices": json.dumps({"crypto:BTCUSDT": current_price})},
        headers=HEADERS,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_buy_position_profits_on_price_rise(client: TestClient) -> None:
    portfolio_id = _seed_portfolio(client)
    _record(client, portfolio_id, type="open", price=100, quantity=2)

    data = _summary(client, portfolio_id, current_price=110)
    assert len(data["positions"]) == 1
    pos = data["positions"][0]
    assert pos["side"] == "buy"
    assert pos["total_quantity"] == 2
    assert pos["avg_price"] == 100
    assert pos["current_price"] == 110
    assert pos["pnl"] == pytest.approx(20)
    assert pos["pnl_percent"] == pytest.approx(10)
    assert data["total_pnl"] == pytest.approx(20)


def test_sell_position_profits_on_price_fall(client: TestClient) -> None:
    portfolio_id = _seed_portfolio(client)
    _record(client, portfolio_id, side="sell", type="open", price=100, quantity=2)

    data = _summary(client, portfolio_id, current_price=90)
    assert len(data["positions"]) == 1
    pos = data["positions"][0]
    assert pos["side"] == "sell"
    assert pos["pnl"] == pytest.approx(20)
    assert pos["pnl_percent"] == pytest.approx(10)


def test_summary_without_current_price_uses_avg(client: TestClient) -> None:
    portfolio_id = _seed_portfolio(client)
    _record(client, portfolio_id, type="open", price=100, quantity=2)

    resp = client.get(
        f"/api/v1/trading/portfolios/{portfolio_id}/summary",
        headers=HEADERS,
    )
    assert resp.status_code == 200
    pos = resp.json()["positions"][0]
    assert pos["current_price"] is None
    assert pos["pnl"] is None