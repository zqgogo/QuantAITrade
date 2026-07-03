"""Agent-owned day/week/month/year summaries."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

from .audit import agent_auditor
from .database import agent_db


class AgentAnalyzer:
    PERIODS = {"day", "week", "month", "year"}

    def summarize_period(
        self,
        period: str = "month",
        date: str | None = None,
        **filters: Any,
    ) -> Dict[str, Any]:
        if period not in self.PERIODS:
            raise ValueError(f"Unsupported period: {period}")
        start, end = self._period_bounds(period, date)
        start_ts = int(start.timestamp())
        end_ts = int(end.timestamp())

        decisions = agent_auditor.query("decisions", limit=10000, start_ts=start_ts, end_ts=end_ts, **filters)["items"]
        trades = agent_auditor.query("trades", limit=10000, start_ts=start_ts, end_ts=end_ts, **filters)["items"]
        positions = agent_auditor.query("positions", limit=10000, start_ts=start_ts, end_ts=end_ts, **filters)["items"]

        realized_pnl = sum(float(row.get("realized_pnl") or 0) for row in trades)
        fees = sum(float(row.get("fees") or 0) for row in trades)
        wins = sum(1 for row in trades if float(row.get("realized_pnl") or 0) > 0)
        losses = sum(1 for row in trades if float(row.get("realized_pnl") or 0) < 0)
        action_counts = self._counts(decisions, "action")
        symbol_counts = self._counts(trades or decisions, "symbol")
        feedback_counts = self._feedback_counts([row["decision_id"] for row in decisions])

        return {
            "period": period,
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "filters": {k: v for k, v in filters.items() if v is not None},
            "decision_count": len(decisions),
            "trade_count": len(trades),
            "open_position_count": sum(1 for row in positions if row.get("status") == "open"),
            "closed_position_count": sum(1 for row in positions if row.get("status") == "closed"),
            "realized_pnl": realized_pnl,
            "fees": fees,
            "net_pnl": realized_pnl - fees,
            "win_count": wins,
            "loss_count": losses,
            "win_rate": wins / len(trades) if trades else 0.0,
            "action_counts": action_counts,
            "symbol_counts": symbol_counts,
            "feedback_counts": feedback_counts,
        }

    def _period_bounds(self, period: str, date: str | None) -> Tuple[datetime, datetime]:
        base = datetime.now(timezone.utc) if date is None else datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        if period == "day":
            start = base.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1) - timedelta(seconds=1)
        elif period == "week":
            start = (base - timedelta(days=base.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7) - timedelta(seconds=1)
        elif period == "month":
            start = base.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(month=start.month + 1)
            end = next_month - timedelta(seconds=1)
        else:
            start = base.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(year=start.year + 1) - timedelta(seconds=1)
        return start, end

    def _counts(self, rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for row in rows:
            value = row.get(key) or "unknown"
            counts[value] = counts.get(value, 0) + 1
        return counts

    def _feedback_counts(self, decision_ids: List[str]) -> Dict[str, int]:
        if not decision_ids:
            return {}
        placeholders = ",".join("?" for _ in decision_ids)
        rows = agent_db.connect().execute(
            f"SELECT feedback_type, COUNT(*) AS count FROM agent_feedback WHERE decision_id IN ({placeholders}) GROUP BY feedback_type",
            decision_ids,
        ).fetchall()
        return {row["feedback_type"]: int(row["count"]) for row in rows}


agent_analyzer = AgentAnalyzer()

