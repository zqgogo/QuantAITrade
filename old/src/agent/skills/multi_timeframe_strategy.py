"""Multi-timeframe market analysis skill."""

from typing import Any, Dict

from .base import AgentSkill


class MultiTimeframeStrategySkill(AgentSkill):
    name = "multi_timeframe_strategy"
    description = "Analyze multi-timeframe trend, momentum, volatility and long/short scenarios."

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        market = payload.get("market", {})
        frames = market.get("timeframes") or {"primary": market}
        frame_votes = {}
        bullish = 0.0
        bearish = 0.0
        available = 0

        for name, frame in frames.items():
            if frame.get("data_points", 0) <= 0:
                continue
            score = float(frame.get("score", 0.0))
            weight = self._timeframe_weight(name)
            frame_votes[name] = {
                "score": score,
                "weighted_score": round(score * weight, 4),
                "trend": frame.get("trend", "unknown"),
                "regime": frame.get("regime", "unknown"),
                "rsi": frame.get("rsi"),
                "macd_histogram": (frame.get("macd") or {}).get("histogram"),
                "volume_ratio": frame.get("volume_ratio"),
            }
            available += 1
            if score > 0:
                bullish += score * weight
            elif score < 0:
                bearish += abs(score) * weight

        primary = market.get("timeframes", {}).get("1h") or market
        latest = primary.get("latest_price") or market.get("latest_price")
        atr_value = primary.get("atr") or market.get("atr")
        support = primary.get("support") or market.get("support")
        resistance = primary.get("resistance") or market.get("resistance")
        total = bullish + bearish
        direction_score = (bullish - bearish) / total if total else 0.0

        return {
            "latest_price": latest,
            "available_timeframes": available,
            "frame_votes": frame_votes,
            "bullish_score": round(bullish, 4),
            "bearish_score": round(bearish, 4),
            "direction_score": round(direction_score, 4),
            "market_bias": self._market_bias(direction_score, available),
            "regime": primary.get("regime", market.get("regime", "unknown")),
            "rsi": primary.get("rsi", market.get("rsi")),
            "atr": atr_value,
            "atr_percent": primary.get("atr_percent", market.get("atr_percent")),
            "support": support,
            "resistance": resistance,
            "risk_reward": self._risk_reward(latest, support, resistance),
            "long_plan": self._scenario_plan("long", latest, support, resistance, atr_value),
            "short_plan": self._scenario_plan("short", latest, support, resistance, atr_value),
            "skill": self.name,
        }

    def _scenario_plan(
        self,
        side: str,
        latest: float | None,
        support: float | None,
        resistance: float | None,
        atr_value: float | None,
    ) -> Dict[str, Any]:
        if not latest:
            return {"entry_zone": [], "invalidation": None, "targets": [], "invalidation_reason": "无价格"}
        atr_fallback = latest * 0.02
        atr_used = atr_value or atr_fallback
        if side == "long":
            entry_low = support if support else latest - atr_used * 0.5
            entry_high = latest + atr_used * 0.25
            invalidation = min(entry_low, latest - atr_used * 1.2)
            targets = sorted([resistance or latest + atr_used * 2, latest + atr_used * 3])
            reason = "跌破支撑或 1.2 ATR，说明多头结构失效"
        else:
            entry_low = latest - atr_used * 0.25
            entry_high = resistance if resistance else latest + atr_used * 0.5
            invalidation = max(entry_high, latest + atr_used * 1.2)
            targets = sorted([support or latest - atr_used * 2, latest - atr_used * 3], reverse=True)
            reason = "突破压力或 1.2 ATR，说明空头结构失效"
        return {
            "entry_zone": [round(entry_low, 8), round(entry_high, 8)],
            "invalidation": round(invalidation, 8),
            "targets": [round(value, 8) for value in targets],
            "invalidation_reason": reason,
        }

    def _market_bias(self, direction_score: float, available: int) -> str:
        if available < 2:
            return "insufficient_data"
        if direction_score >= 0.25:
            return "bullish"
        if direction_score <= -0.25:
            return "bearish"
        return "neutral"

    def _risk_reward(self, latest: float | None, support: float | None, resistance: float | None) -> Dict[str, Any]:
        if not latest or not support or not resistance:
            return {"long": None, "short": None}
        long_risk = max(latest - support, 0)
        long_reward = max(resistance - latest, 0)
        short_risk = max(resistance - latest, 0)
        short_reward = max(latest - support, 0)
        return {
            "long": round(long_reward / long_risk, 4) if long_risk else None,
            "short": round(short_reward / short_risk, 4) if short_risk else None,
        }

    def _timeframe_weight(self, name: str) -> float:
        return {"15m": 0.7, "1h": 1.0, "4h": 1.2, "1d": 1.4, "primary": 1.0}.get(name, 1.0)

