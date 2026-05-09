"""Agent-owned audit queries."""

from typing import Any, Dict, List

from .database import agent_db


class AgentAuditor:
    """Query all agent-owned records with common filters."""

    TABLES = {
        "decisions": ("agent_decisions", "created_at"),
        "feedback": ("agent_feedback", "created_at"),
        "trades": ("agent_trade_records", "traded_at"),
        "positions": ("agent_positions", "opened_at"),
        "memories": ("agent_memories", "created_at"),
        "reports": ("agent_reports", "created_at"),
    }

    COMMON_FILTERS = {
        "agent_decisions": {"run_env", "agent_id", "portfolio_id", "account_id", "position_group_id", "strategy_id", "symbol", "action", "status"},
        "agent_trade_records": {"run_env", "portfolio_id", "account_id", "position_group_id", "strategy_id", "symbol", "side", "status", "source_type"},
        "agent_positions": {"run_env", "portfolio_id", "account_id", "position_group_id", "strategy_id", "symbol", "side", "status"},
        "agent_memories": {"agent_id", "memory_type"},
        "agent_feedback": {"decision_id", "feedback_type"},
        "agent_reports": {"agent_id", "run_env", "report_type"},
    }

    def query(
        self,
        record_type: str = "decisions",
        limit: int = 100,
        offset: int = 0,
        start_ts: int | None = None,
        end_ts: int | None = None,
        **filters: Any,
    ) -> Dict[str, Any]:
        if record_type not in self.TABLES:
            raise ValueError(f"Unsupported audit record type: {record_type}")

        agent_db.init_database()
        table, time_col = self.TABLES[record_type]
        clauses: List[str] = []
        params: List[Any] = []

        if start_ts is not None:
            clauses.append(f"{time_col} >= ?")
            params.append(start_ts)
        if end_ts is not None:
            clauses.append(f"{time_col} <= ?")
            params.append(end_ts)

        allowed = self.COMMON_FILTERS.get(table, set())
        for key, value in filters.items():
            if value is None or key not in allowed:
                continue
            clauses.append(f"{key} = ?")
            params.append(value)

        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        count_row = agent_db.connect().execute(
            f"SELECT COUNT(*) AS total FROM {table} {where}", params
        ).fetchone()
        rows = agent_db.connect().execute(
            f"SELECT * FROM {table} {where} ORDER BY {time_col} DESC LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()
        return {
            "record_type": record_type,
            "total": int(count_row["total"] if count_row else 0),
            "limit": limit,
            "offset": offset,
            "items": [dict(row) for row in rows],
            "filters": {k: v for k, v in filters.items() if v is not None},
            "start_ts": start_ts,
            "end_ts": end_ts,
        }


agent_auditor = AgentAuditor()

