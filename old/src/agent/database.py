"""SQLite repository owned by the agent package."""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import AGENT_DB_PATH
from .schemas import AgentDecision, AgentFeedback, AgentPosition, AgentTradeRecord, utc_ts


class AgentDatabase:
    """Agent-local durable store.

    The database file lives under ``src/agent/data/agent.db`` by default so
    decisions, memory, preferences, reports, trades and positions travel with
    the agent package.
    """

    def __init__(self, db_path: Path = AGENT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA busy_timeout=30000")
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def init_database(self) -> None:
        conn = self.connect()
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS agent_profile (
                agent_id TEXT PRIMARY KEY,
                display_name TEXT,
                preferences_json TEXT,
                traits_json TEXT,
                updated_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agent_memories (
                memory_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                summary TEXT NOT NULL,
                payload_json TEXT,
                importance REAL DEFAULT 0.5,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agent_decisions (
                decision_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                run_env TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                portfolio_id TEXT NOT NULL,
                account_id TEXT NOT NULL,
                position_group_id TEXT NOT NULL,
                strategy_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                asset_class TEXT NOT NULL,
                exchange_name TEXT,
                action TEXT NOT NULL,
                confidence REAL NOT NULL,
                reasoning TEXT,
                risk_notes TEXT,
                suggested_price REAL,
                suggested_quantity REAL,
                timeframe TEXT,
                stop_loss_json TEXT,
                take_profit_json TEXT,
                requires_human_confirmation INTEGER NOT NULL,
                status TEXT NOT NULL,
                market_snapshot_json TEXT,
                portfolio_snapshot_json TEXT,
                risk_snapshot_json TEXT,
                memory_snapshot_json TEXT,
                metadata_json TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_agent_decisions_scope
            ON agent_decisions(run_env, portfolio_id, account_id, position_group_id, symbol, created_at DESC);

            CREATE TABLE IF NOT EXISTS agent_feedback (
                feedback_id TEXT PRIMARY KEY,
                decision_id TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                comment TEXT,
                executed_price REAL,
                executed_quantity REAL,
                result_snapshot_json TEXT,
                created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agent_trade_records (
                trade_id TEXT PRIMARY KEY,
                run_env TEXT NOT NULL,
                portfolio_id TEXT NOT NULL,
                account_id TEXT NOT NULL,
                position_group_id TEXT NOT NULL,
                strategy_id TEXT NOT NULL,
                decision_id TEXT,
                symbol TEXT NOT NULL,
                asset_class TEXT NOT NULL,
                side TEXT NOT NULL,
                price REAL NOT NULL,
                quantity REAL NOT NULL,
                status TEXT NOT NULL,
                source_type TEXT NOT NULL,
                realized_pnl REAL DEFAULT 0.0,
                fees REAL DEFAULT 0.0,
                notes TEXT,
                traded_at INTEGER NOT NULL,
                created_at INTEGER NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_agent_trades_scope
            ON agent_trade_records(run_env, portfolio_id, account_id, position_group_id, symbol, traded_at DESC);

            CREATE TABLE IF NOT EXISTS agent_positions (
                position_id TEXT PRIMARY KEY,
                run_env TEXT NOT NULL,
                portfolio_id TEXT NOT NULL,
                account_id TEXT NOT NULL,
                position_group_id TEXT NOT NULL,
                strategy_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                asset_class TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_price REAL NOT NULL,
                quantity REAL NOT NULL,
                status TEXT NOT NULL,
                realized_pnl REAL DEFAULT 0.0,
                unrealized_pnl REAL DEFAULT 0.0,
                max_drawdown REAL DEFAULT 0.0,
                opened_at INTEGER NOT NULL,
                closed_at INTEGER,
                notes TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_agent_positions_scope
            ON agent_positions(run_env, portfolio_id, account_id, position_group_id, symbol, status);

            CREATE TABLE IF NOT EXISTS agent_reports (
                report_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                run_env TEXT NOT NULL,
                report_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                filters_json TEXT,
                created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agent_performance_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                run_env TEXT NOT NULL,
                portfolio_id TEXT NOT NULL,
                account_id TEXT,
                position_group_id TEXT,
                strategy_id TEXT,
                symbol TEXT,
                period_type TEXT NOT NULL,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                metrics_json TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );
            """
        )
        conn.commit()

    def save_decision(self, decision: AgentDecision) -> None:
        self.init_database()
        data = decision.to_dict()
        conn = self.connect()
        conn.execute(
            """
            INSERT OR REPLACE INTO agent_decisions (
                decision_id, request_id, run_env, agent_id, portfolio_id, account_id,
                position_group_id, strategy_id, symbol, asset_class, exchange_name,
                action, confidence, reasoning, risk_notes, suggested_price,
                suggested_quantity, timeframe, stop_loss_json, take_profit_json,
                requires_human_confirmation, status, market_snapshot_json,
                portfolio_snapshot_json, risk_snapshot_json, memory_snapshot_json,
                metadata_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["decision_id"], data["request_id"], data["run_env"], data["agent_id"],
                data["portfolio_id"], data["account_id"], data["position_group_id"],
                data["strategy_id"], data["symbol"], data["asset_class"], data["exchange"],
                data["action"], data["confidence"], data["reasoning"], data["risk_notes"],
                data["suggested_price"], data["suggested_quantity"], data["timeframe"],
                json.dumps(data["stop_loss"], ensure_ascii=False),
                json.dumps(data["take_profit"], ensure_ascii=False),
                1 if data["requires_human_confirmation"] else 0,
                data["status"],
                json.dumps(data["market_snapshot"], ensure_ascii=False),
                json.dumps(data["portfolio_snapshot"], ensure_ascii=False),
                json.dumps(data["risk_snapshot"], ensure_ascii=False),
                json.dumps(data["memory_snapshot"], ensure_ascii=False),
                json.dumps(data["metadata"], ensure_ascii=False),
                data["created_at"], data["updated_at"],
            ),
        )
        conn.commit()

    def get_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        self.init_database()
        row = self.connect().execute(
            "SELECT * FROM agent_decisions WHERE decision_id = ?", (decision_id,)
        ).fetchone()
        return self._decode_decision_row(row) if row else None

    def list_decisions(self, limit: int = 50, **filters: Any) -> List[Dict[str, Any]]:
        self.init_database()
        clauses = []
        params: List[Any] = []
        for key in ("run_env", "portfolio_id", "account_id", "position_group_id", "symbol", "status"):
            value = filters.get(key)
            if value:
                clauses.append(f"{key} = ?")
                params.append(value)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(limit)
        rows = self.connect().execute(
            f"SELECT * FROM agent_decisions {where} ORDER BY created_at DESC LIMIT ?", params
        ).fetchall()
        return [self._decode_decision_row(row) for row in rows]

    def save_feedback(self, feedback: AgentFeedback) -> None:
        self.init_database()
        conn = self.connect()
        conn.execute(
            """
            INSERT INTO agent_feedback (
                feedback_id, decision_id, feedback_type, comment, executed_price,
                executed_quantity, result_snapshot_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                feedback.feedback_id, feedback.decision_id, feedback.feedback_type,
                feedback.comment, feedback.executed_price, feedback.executed_quantity,
                json.dumps(feedback.result_snapshot, ensure_ascii=False), feedback.created_at,
            ),
        )
        status = {
            "accepted": "accepted",
            "rejected": "rejected",
            "modified": "modified",
            "executed_manually": "executed",
            "ignored": "rejected",
        }.get(feedback.feedback_type, "pending")
        conn.execute(
            "UPDATE agent_decisions SET status = ?, updated_at = ? WHERE decision_id = ?",
            (status, utc_ts(), feedback.decision_id),
        )
        conn.commit()

    def save_trade(self, trade: AgentTradeRecord) -> None:
        self.init_database()
        data = trade.to_dict()
        self.connect().execute(
            """
            INSERT OR REPLACE INTO agent_trade_records (
                trade_id, run_env, portfolio_id, account_id, position_group_id,
                strategy_id, decision_id, symbol, asset_class, side, price, quantity,
                status, source_type, realized_pnl, fees, notes, traded_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["trade_id"], data["run_env"], data["portfolio_id"], data["account_id"],
                data["position_group_id"], data["strategy_id"], data["decision_id"],
                data["symbol"], data["asset_class"], data["side"], data["price"],
                data["quantity"], data["status"], data["source_type"], data["realized_pnl"],
                data["fees"], data["notes"], data["traded_at"], data["created_at"],
            ),
        )
        self.connect().commit()

    def save_position(self, position: AgentPosition) -> None:
        self.init_database()
        data = position.to_dict()
        self.connect().execute(
            """
            INSERT OR REPLACE INTO agent_positions (
                position_id, run_env, portfolio_id, account_id, position_group_id,
                strategy_id, symbol, asset_class, side, entry_price, quantity, status,
                realized_pnl, unrealized_pnl, max_drawdown, opened_at, closed_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["position_id"], data["run_env"], data["portfolio_id"], data["account_id"],
                data["position_group_id"], data["strategy_id"], data["symbol"],
                data["asset_class"], data["side"], data["entry_price"], data["quantity"],
                data["status"], data["realized_pnl"], data["unrealized_pnl"],
                data["max_drawdown"], data["opened_at"], data["closed_at"], data["notes"],
            ),
        )
        self.connect().commit()

    def list_positions(self, limit: int = 100, **filters: Any) -> List[Dict[str, Any]]:
        self.init_database()
        clauses = []
        params: List[Any] = []
        for key in ("run_env", "portfolio_id", "account_id", "position_group_id", "symbol", "status"):
            value = filters.get(key)
            if value:
                clauses.append(f"{key} = ?")
                params.append(value)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        params.append(limit)
        rows = self.connect().execute(
            f"SELECT * FROM agent_positions {where} ORDER BY opened_at DESC LIMIT ?", params
        ).fetchall()
        return [dict(row) for row in rows]

    def summarize_performance(self, **filters: Any) -> Dict[str, Any]:
        self.init_database()
        clauses = []
        params: List[Any] = []
        for key in ("run_env", "portfolio_id", "account_id", "position_group_id", "symbol", "strategy_id"):
            value = filters.get(key)
            if value:
                clauses.append(f"{key} = ?")
                params.append(value)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        rows = self.connect().execute(
            f"SELECT side, realized_pnl, fees FROM agent_trade_records {where}", params
        ).fetchall()
        pnl = sum(float(row["realized_pnl"] or 0) for row in rows)
        fees = sum(float(row["fees"] or 0) for row in rows)
        wins = sum(1 for row in rows if float(row["realized_pnl"] or 0) > 0)
        trade_count = len(rows)
        return {
            "trade_count": trade_count,
            "realized_pnl": pnl,
            "fees": fees,
            "net_pnl": pnl - fees,
            "win_rate": wins / trade_count if trade_count else 0.0,
            "filters": filters,
        }

    def _decode_decision_row(self, row: sqlite3.Row) -> Dict[str, Any]:
        data = dict(row)
        mapping = {
            "exchange_name": "exchange",
            "stop_loss_json": "stop_loss",
            "take_profit_json": "take_profit",
            "market_snapshot_json": "market_snapshot",
            "portfolio_snapshot_json": "portfolio_snapshot",
            "risk_snapshot_json": "risk_snapshot",
            "memory_snapshot_json": "memory_snapshot",
            "metadata_json": "metadata",
        }
        for old_key, new_key in mapping.items():
            value = data.pop(old_key, None)
            if old_key.endswith("_json"):
                data[new_key] = json.loads(value) if value else {}
            else:
                data[new_key] = value
        data["requires_human_confirmation"] = bool(data["requires_human_confirmation"])
        return data


agent_db = AgentDatabase()
