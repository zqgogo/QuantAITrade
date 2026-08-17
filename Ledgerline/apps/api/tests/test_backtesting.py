import pytest
from fastapi.testclient import TestClient

from app.main import app

HEADERS = {"X-API-Key": "dev-secret-key"}


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


def _seed_market(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/market/ohlcv/refresh",
        params={"market": "crypto", "symbol": "BTCUSDT", "interval": "1d", "limit": 50},
        headers=HEADERS,
    )
    assert resp.status_code == 200, resp.text


def _quick_run(client: TestClient) -> dict:
    resp = client.post(
        "/api/v1/backtesting/quick-run",
        params={
            "strategy": "rsi",
            "market": "crypto",
            "symbol": "BTCUSDT",
            "interval": "1d",
            "initial_capital": 10000,
        },
        headers=HEADERS,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_backtest_runs_and_is_saved(client: TestClient) -> None:
    _seed_market(client)
    result = _quick_run(client)

    assert result["success"] is True
    assert result["strategy_name"] == "rsi"

    resp = client.get(
        "/api/v1/backtesting/results",
        params={"limit": 20},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    backtests = resp.json()["backtests"]
    assert len(backtests) >= 1
    assert backtests[0]["strategy_name"] == "rsi"
    assert backtests[0]["total_return"] == pytest.approx(result["metrics"]["total_return"])
    assert backtests[0]["total_trades"] == result["metrics"]["total_trades"]


def test_backtest_results_returns_empty_without_runs(client: TestClient) -> None:
    resp = client.get(
        "/api/v1/backtesting/results",
        params={"limit": 20},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["backtests"] == []