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
    workspace_id = resp.json()["id"]
    resp = client.post(
        "/api/v1/trading/portfolios",
        json={"workspace_id": workspace_id, "name": "pf"},
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


def _stats(client: TestClient, period: str):
    return client.get("/api/v1/trading/reports/stats", params={"period": period}, headers=HEADERS)


def test_empty_reports(client: TestClient) -> None:
    resp = _stats(client, "all")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_trades"] == 0
    assert data["total_buy"] == 0
    assert data["total_sell"] == 0
    assert data["total_fee"] == 0
    assert data["realized_pnl"] == 0
    assert data["net_volume"] == 0
    assert data["daily"] == []


def test_open_close_pnl_is_net_of_fees(client: TestClient) -> None:
    portfolio_id = _seed_portfolio(client)
    _record(client, portfolio_id, type="open", price=100, quantity=2, fee=1)
    _record(client, portfolio_id, type="close", price=120, quantity=2, fee=1)

    for period in ("week", "month", "all"):
        data = _stats(client, period).json()
        assert data["total_trades"] == 2
        assert data["total_buy"] == 200
        assert data["total_sell"] == 240
        assert data["total_fee"] == 2
        assert data["net_volume"] == 40
        assert data["realized_pnl"] == 38
        assert len(data["daily"]) == 1
        assert data["daily"][0]["pnl"] == 38
        assert data["daily"][0]["fee"] == 2


def test_partial_reduce_then_close(client: TestClient) -> None:
    portfolio_id = _seed_portfolio(client)
    _record(client, portfolio_id, type="open", price=100, quantity=4)
    _record(client, portfolio_id, type="reduce", price=110, quantity=2)
    _record(client, portfolio_id, type="close", price=120, quantity=2)

    data = _stats(client, "all").json()
    assert data["total_trades"] == 3
    assert data["total_buy"] == 400
    assert data["total_sell"] == 460
    assert data["realized_pnl"] == 60


def test_unclosed_position_not_included(client: TestClient) -> None:
    portfolio_id = _seed_portfolio(client)
    _record(client, portfolio_id, type="open", price=100, quantity=2)

    data = _stats(client, "all").json()
    assert data["total_trades"] == 1
    assert data["total_buy"] == 200
    assert data["realized_pnl"] == 0


def test_invalid_period_returns_422(client: TestClient) -> None:
    resp = _stats(client, "year")
    assert resp.status_code == 422


def test_response_shape(client: TestClient) -> None:
    data = _stats(client, "week").json()
    assert set(data.keys()) >= {
        "period",
        "start_date",
        "end_date",
        "total_trades",
        "total_buy",
        "total_sell",
        "total_fee",
        "realized_pnl",
        "net_volume",
        "daily",
    }