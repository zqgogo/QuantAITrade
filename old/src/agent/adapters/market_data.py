"""Market data adapter.

This adapter may read QuantAITrade's shared market database when available, but
the output is copied into the agent decision snapshot and stored in agent.db.
"""

from typing import Any, Dict, List

from ..tools.indicators import atr, bollinger, macd, moving_average, pct_change, rsi, slope, support_resistance


class MarketDataAdapter:
    def get_snapshot(self, symbol: str, interval: str = "1h", limit: int = 80) -> Dict[str, Any]:
        klines = self._load_klines(symbol, interval, limit)
        return self._build_interval_snapshot(symbol, interval, klines)

    def get_multi_timeframe_snapshot(
        self,
        symbol: str,
        intervals: List[str] | None = None,
        limit: int = 160,
    ) -> Dict[str, Any]:
        intervals = intervals or ["15m", "1h", "4h", "1d"]
        frames = {}
        for interval in intervals:
            snapshot = self.get_snapshot(symbol, interval, limit)
            frames[interval] = snapshot

        available = [item for item in frames.values() if item.get("data_points", 0) > 0]
        primary = frames.get("1h") or (available[0] if available else {"symbol": symbol, "data_points": 0})
        alignment_score = sum(float(item.get("score", 0.0)) for item in available)
        if available:
            alignment_score = alignment_score / len(available)
        return {
            **primary,
            "symbol": symbol,
            "mode": "multi_timeframe",
            "timeframes": frames,
            "alignment_score": alignment_score,
            "available_timeframes": [item["interval"] for item in available],
        }

    def _load_klines(self, symbol: str, interval: str, limit: int) -> List[Dict[str, Any]]:
        try:
            from data.db_manager import db_manager

            klines = db_manager.get_klines(symbol, interval, limit=limit)
        except Exception:
            klines = []

        rows = [dict(row) for row in klines]
        rows.sort(key=lambda item: int(item.get("open_time") or item.get("timestamp") or 0))
        return rows

    def _build_interval_snapshot(self, symbol: str, interval: str, klines: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not klines:
            return {"symbol": symbol, "interval": interval, "data_points": 0}

        opens = [float(row["open"]) for row in klines]
        highs = [float(row["high"]) for row in klines]
        lows = [float(row["low"]) for row in klines]
        closes = [float(row["close"]) for row in klines]
        volumes = [float(row.get("volume", 0) or 0) for row in klines]
        latest = closes[-1]
        ma_fast = moving_average(closes, 5)
        ma_mid = moving_average(closes, 20)
        ma_slow = moving_average(closes, 60)
        change = ((latest / closes[0]) - 1) * 100 if closes[0] else 0.0
        rsi_value = rsi(closes)
        macd_value = macd(closes)
        boll = bollinger(closes)
        atr_value = atr(highs, lows, closes)
        levels = support_resistance(highs, lows)
        volume_ma = moving_average(volumes, 20) or 0
        volume_ratio = volumes[-1] / volume_ma if volume_ma else None
        trend_slope = slope(closes, 30)
        trend = self._classify_trend(latest, ma_fast, ma_mid, ma_slow, trend_slope)
        regime = self._classify_regime(latest, boll, atr_value)
        score = self._score_frame(latest, ma_fast, ma_mid, ma_slow, rsi_value, macd_value, trend_slope, volume_ratio)

        return {
            "symbol": symbol,
            "interval": interval,
            "data_points": len(klines),
            "latest_price": latest,
            "open": opens[-1],
            "high": highs[-1],
            "low": lows[-1],
            "close": latest,
            "volume": volumes[-1],
            "ma_fast": ma_fast,
            "ma_mid": ma_mid,
            "ma_slow": ma_slow,
            "change_percent": change,
            "trend": trend,
            "regime": regime,
            "score": score,
            "rsi": rsi_value,
            "macd": macd_value,
            "bollinger": boll,
            "atr": atr_value,
            "atr_percent": (atr_value / latest * 100) if atr_value and latest else None,
            "support": levels["support"],
            "resistance": levels["resistance"],
            "volume_ratio": volume_ratio,
            "slope": trend_slope,
            "recent_bars": klines[-20:],
        }

    def _classify_trend(
        self,
        latest: float,
        ma_fast: float | None,
        ma_mid: float | None,
        ma_slow: float | None,
        trend_slope: float | None,
    ) -> str:
        if not ma_fast or not ma_mid:
            return "unknown"
        if ma_slow and latest > ma_fast > ma_mid > ma_slow and (trend_slope or 0) > 0:
            return "strong_up"
        if latest > ma_fast > ma_mid:
            return "up"
        if ma_slow and latest < ma_fast < ma_mid < ma_slow and (trend_slope or 0) < 0:
            return "strong_down"
        if latest < ma_fast < ma_mid:
            return "down"
        return "range"

    def _classify_regime(self, latest: float, boll: Dict[str, Any], atr_value: float | None) -> str:
        position = boll.get("position")
        atr_percent = (atr_value / latest * 100) if atr_value and latest else None
        if atr_percent and atr_percent > 4:
            return "high_volatility"
        if position is not None and 0.25 <= position <= 0.75:
            return "range_middle"
        if position is not None and position > 0.9:
            return "upper_breakout_or_overbought"
        if position is not None and position < 0.1:
            return "lower_breakdown_or_oversold"
        return "normal"

    def _score_frame(
        self,
        latest: float,
        ma_fast: float | None,
        ma_mid: float | None,
        ma_slow: float | None,
        rsi_value: float | None,
        macd_value: Dict[str, Any],
        trend_slope: float | None,
        volume_ratio: float | None,
    ) -> float:
        score = 0.0
        if ma_fast and ma_mid:
            score += 1.0 if ma_fast > ma_mid else -1.0
        if ma_mid and ma_slow:
            score += 1.0 if ma_mid > ma_slow else -1.0
        if ma_fast:
            score += 0.5 if latest > ma_fast else -0.5
        if rsi_value is not None:
            if 45 <= rsi_value <= 65:
                score += 0.3
            elif rsi_value > 72:
                score -= 0.6
            elif rsi_value < 28:
                score += 0.4
        histogram = macd_value.get("histogram")
        if histogram is not None:
            score += 0.6 if histogram > 0 else -0.6
        if trend_slope is not None:
            score += 0.5 if trend_slope > 0 else -0.5
        if volume_ratio and volume_ratio > 1.2:
            score *= 1.1
        return round(max(min(score, 4.0), -4.0), 4)


market_data_adapter = MarketDataAdapter()
