import json

import pytest
from fastapi.testclient import TestClient

from app.main import app

HEADERS = {"X-API-Key": "dev-secret-key"}


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


def _seed_portfolio(client: TestClient, currency: str = "USD") -> int:
    resp = client.post("/api/v1/trading/workspaces", json={"name": "ws"}, headers=HEADERS)
    assert resp.status_code == 200
    resp = client.post(
        "/api/v1/trading/portfolios",
        json={"workspace_id": resp.json()["id"], "name": "pf", "currency": currency},
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


def test_summary_aggregates_total_fee(client: TestClient) -> None:
    portfolio_id = _seed_portfolio(client)
    _record(client, portfolio_id, type="open", price=100, quantity=2, fee=1.5)
    _record(client, portfolio_id, type="add", price=110, quantity=1, fee=0.5)

    data = _summary(client, portfolio_id, current_price=105)
    assert data["positions"][0]["total_fee"] == pytest.approx(2.0)
    assert data["positions"][0]["total_amount"] == pytest.approx(310)


def test_reduce_exceeding_quantity_rejected(client: TestClient) -> None:
    portfolio_id = _seed_portfolio(client)
    _record(client, portfolio_id, type="open", price=100, quantity=2)

    resp = client.post(
        "/api/v1/trading/transactions",
        json={
            "portfolio_id": portfolio_id,
            "market": "crypto",
            "symbol": "BTCUSDT",
            "side": "buy",
            "type": "reduce",
            "price": 120,
            "quantity": 3,
        },
        headers=HEADERS,
    )
    assert resp.status_code == 400
    assert "quantity" in resp.json()["detail"].lower()


def test_close_exceeding_quantity_rejected(client: TestClient) -> None:
    portfolio_id = _seed_portfolio(client)
    _record(client, portfolio_id, type="open", price=100, quantity=2)

    resp = client.post(
        "/api/v1/trading/transactions",
        json={
            "portfolio_id": portfolio_id,
            "market": "crypto",
            "symbol": "BTCUSDT",
            "side": "buy",
            "type": "close",
            "price": 120,
            "quantity": 5,
        },
        headers=HEADERS,
    )
    assert resp.status_code == 400


def test_partial_reduce_then_close(client: TestClient) -> None:
    portfolio_id = _seed_portfolio(client)
    _record(client, portfolio_id, type="open", price=100, quantity=3)
    _record(client, portfolio_id, type="reduce", price=110, quantity=1)

    resp = client.post(
        "/api/v1/trading/transactions",
        json={
            "portfolio_id": portfolio_id,
            "market": "crypto",
            "symbol": "BTCUSDT",
            "side": "buy",
            "type": "close",
            "price": 120,
            "quantity": 2,
        },
        headers=HEADERS,
    )
    assert resp.status_code == 200
    data = _summary(client, portfolio_id, current_price=120)
    assert data["positions"] == []


def test_reduce_without_open_position_rejected(client: TestClient) -> None:
    portfolio_id = _seed_portfolio(client)

    resp = client.post(
        "/api/v1/trading/transactions",
        json={
            "portfolio_id": portfolio_id,
            "market": "crypto",
            "symbol": "BTCUSDT",
            "side": "buy",
            "type": "close",
            "price": 120,
            "quantity": 1,
        },
        headers=HEADERS,
    )
    assert resp.status_code == 400


def test_non_positive_quantity_rejected(client: TestClient) -> None:
    portfolio_id = _seed_portfolio(client)

    resp = client.post(
        "/api/v1/trading/transactions",
        json={
            "portfolio_id": portfolio_id,
            "market": "crypto",
            "symbol": "BTCUSDT",
            "side": "buy",
            "type": "open",
            "price": 100,
            "quantity": 0,
        },
        headers=HEADERS,
    )
    assert resp.status_code == 400


def test_transaction_list_returns_real_fee(client: TestClient) -> None:
    portfolio_id = _seed_portfolio(client)
    _record(client, portfolio_id, type="open", price=100, quantity=2, fee=1.5)

    resp = client.get(
        "/api/v1/trading/transactions",
        params={"portfolio_id": portfolio_id},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()[0]["fee"] == pytest.approx(1.5)


def test_summary_converts_value_to_portfolio_currency(client: TestClient) -> None:
    portfolio_id = _seed_portfolio(client, currency="CNYT")
    _record(client, portfolio_id, type="open", price=100, quantity=2)

    resp = client.post(
        "/api/v1/trading/exchange-rates",
        json={"from_currency": "CNYT", "to_currency": "USD", "rate": 0.14},
        headers=HEADERS,
    )
    assert resp.status_code == 200

    # BTCUSDT position is USD-quoted (USDT normalized to USD); portfolio base is CNYT.
    # 200 USD = 200 / 0.14 ≈ 1428.57 CNYT
    data = _summary(client, portfolio_id, current_price=100)
    assert data["currency"] == "CNYT"
    assert data["total_value"] == pytest.approx(200 / 0.14)
    assert data["positions"][0]["total_amount"] == pytest.approx(200 / 0.14)
    assert data["positions"][0]["currency"] == "CNYT"


def test_summary_without_rate_uses_raw_value(client: TestClient) -> None:
    portfolio_id = _seed_portfolio(client, currency="CNYT")
    _record(client, portfolio_id, type="open", price=100, quantity=2)

    data = _summary(client, portfolio_id, current_price=100)
    assert data["currency"] == "CNYT"
    assert data["total_value"] == pytest.approx(200)


def test_fx_rate_crud(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/trading/exchange-rates",
        json={"from_currency": "cnyt", "to_currency": "usd", "rate": 0.14},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["from_currency"] == "CNYT"

    resp = client.get("/api/v1/trading/exchange-rates", headers=HEADERS)
    assert resp.status_code == 200
    assert any(r["from_currency"] == "CNYT" and r["to_currency"] == "USD" for r in resp.json())

    resp = client.delete(
        "/api/v1/trading/exchange-rates",
        params={"from_currency": "CNYT", "to_currency": "USD"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    resp = client.get("/api/v1/trading/exchange-rates", headers=HEADERS)
    assert all(r["from_currency"] != "CNYT" for r in resp.json())


def test_fx_rate_rejects_same_currency(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/trading/exchange-rates",
        json={"from_currency": "USD", "to_currency": "USD", "rate": 1},
        headers=HEADERS,
    )
    assert resp.status_code == 400