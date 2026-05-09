"""Risk review skill for agent suggestions."""

from typing import Any, Dict, List

from .base import AgentSkill


class RiskReviewSkill(AgentSkill):
    name = "risk_review"
    description = "Review analysis quality, volatility risk and overbought/oversold warnings."

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        analysis = payload.get("analysis", {})
        action = payload.get("action", "OBSERVE")
        warnings: List[str] = []

        if analysis.get("available_timeframes", 0) < 3:
            warnings.append("有效周期不足，置信度需下调")
        if analysis.get("atr_percent") and analysis["atr_percent"] > 4:
            warnings.append("波动率偏高，建议降低仓位")
        if analysis.get("rsi") and analysis["rsi"] > 75 and action == "BUY":
            warnings.append("RSI 过热，不适合追高")
        if analysis.get("rsi") and analysis["rsi"] < 25 and action == "SELL":
            warnings.append("RSI 过冷，不适合追空")

        rr = analysis.get("risk_reward") or {}
        return {
            "warnings": warnings,
            "risk_reward": rr,
            "summary": f"多头盈亏比={self._fmt(rr.get('long'))}，空头盈亏比={self._fmt(rr.get('short'))}",
            "skill": self.name,
        }

    def _fmt(self, value: object) -> str:
        if value is None:
            return "N/A"
        if isinstance(value, float):
            return f"{value:.4f}"
        return str(value)

