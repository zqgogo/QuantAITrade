"""Market data adapter.

This adapter may read QuantAITrade's shared market database when available, but
the output is copied into the agent decision snapshot and stored in agent.db.
"""

from typing import Any, Dict


class MarketDataAdapter:
    def get_snapshot(self, symbol: str, interval: str = "1h", limit: int = 80) -> Dict[str, Any]:
        try:
            from data.db_manager import db_manager

            klines = db_manager.get_klines(symbol, interval, limit=limit)
        except Exception:
            klines = []

        if not klines:
            return {"symbol": symbol, "interval": interval, "data_points": 0}

        closes = [float(row["close"] if isinstance(row, dict) else row["close"]) for row in klines]
        latest = closes[-1]
        ma_fast = sum(closes[-5:]) / min(5, len(closes))
        ma_slow = sum(closes[-20:]) / min(20, len(closes))
        change = ((latest / closes[0]) - 1) * 100 if closes[0] else 0.0
        return {
            "symbol": symbol,
            "interval": interval,
            "data_points": len(klines),
            "latest_price": latest,
            "ma_fast": ma_fast,
            "ma_slow": ma_slow,
            "change_percent": change,
            "trend": "up" if ma_fast > ma_slow else "down" if ma_fast < ma_slow else "flat",
        }


market_data_adapter = MarketDataAdapter()

